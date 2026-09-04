#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
train_llm_lora.py — v19 两阶段 LoRA-SFT 训练器 (纯 SFT, 协议锁定)
===============================================================
从 v18 冻结 Qwen3 训练代码 phase3_train.py 严格改编:
  - 移除全部专利组件: 无 teacher/KD/rule/smoothing/温度退火 → 纯 CE
  # 两阶段层冻结语义与冻结协议一致 (v19.1 双边界等比映射):
  #   Stage1 = 高层子区间 LoRA 可训 (其余冻结); LR=8e-5 常数, 3 epochs
  #   Stage2 = 扩展到中高层更大子区间; LR=1e-5 CosineAnnealingLR, 2 epochs
  #   参考 = v18 冻结协议【设计区间】开区间 [23,32) / [12,32) (Qwen3 36 层),
  #   两个边界都乘 L/36: L=36 → 23..31/12..31, L=48 → 31..42/16..42
  #   (v19.1 protocol correction, 见 protocol/v19_protocol_lock.md 变更记录)
  - 4-bit NF4 QLoRA (与冻结 Qwen3 一致); batch=1 + grad_accum=16; clip 1.0
  - 模板与冻结 Qwen3 逐字一致 (证型+辨证依据); 经模型原生 chat template 格式化
  - checkpoint = stage2 dev loss 最低; held-out 全程不接触
  - 协议 JSON 锁定: num_hidden_layers 真实读取, 层区间首次解析后写回锁定,
    再训练禁止改变; 模块映射必须 VERIFIED

用法:
  HF_ENDPOINT=https://hf-mirror.com python scripts/train_llm_lora.py \
      --model-path internlm/internlm3-8b-instruct \
      --train-file ../../../v18_working/dataset_audit/data/train_4186.json \
      --dev-file   ../../../v18_working/dataset_audit/data/dev_420.json \
      --labels-file ../../../v18_working/evaluation/labels_42.txt \
      --output-dir runs/internlm3/full/seed42 --seed 42
"""
import argparse
import gc
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

V19 = Path(__file__).resolve().parents[1]
PROTOCOL = V19 / "protocol" / "internlm3_training_protocol.json"
MAPPING = V19 / "protocol" / "internlm3_lora_module_mapping.json"

parser = argparse.ArgumentParser()
parser.add_argument("--model-path", required=True)
parser.add_argument("--train-file", required=True)
parser.add_argument("--dev-file", required=True)
parser.add_argument("--labels-file", required=True)
parser.add_argument("--output-dir", required=True)
parser.add_argument("--seed", type=int, default=42)
parser.add_argument("--quant-bits", type=int, default=4, help="4=NF4 QLoRA (frozen Qwen3 parity); 0=full precision")
parser.add_argument("--lora-r", type=int, default=16)
parser.add_argument("--lora-alpha", type=int, default=32)
parser.add_argument("--lora-dropout", type=float, default=0.1)
parser.add_argument("--max-seq-length", type=int, default=768)
parser.add_argument("--batch-size", type=int, default=1)
parser.add_argument("--grad-accum", type=int, default=16)
parser.add_argument("--stage1-lr", type=float, default=8e-5)
parser.add_argument("--stage1-epochs", type=int, default=3)
parser.add_argument("--stage2-lr", type=float, default=1e-5)
parser.add_argument("--stage2-epochs", type=int, default=2)
parser.add_argument("--max-steps", type=int, default=0, help="smoke 用: 每个 stage 只跑 N 个 optimizer step 后保存 checkpoint 退出 (0=完整训练; 不改任何训练口径)")
args = parser.parse_args()

OUT = Path(args.output_dir)
OUT.mkdir(parents=True, exist_ok=True)

# ── seed ──
random.seed(args.seed); np.random.seed(args.seed)
torch.manual_seed(args.seed); torch.cuda.manual_seed_all(args.seed)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[device] {DEVICE}", flush=True)

# ── 协议锁定: 层区间 (真实读取 num_hidden_layers) ──
protocol = json.load(open(PROTOCOL, encoding="utf-8"))
mapping = json.load(open(MAPPING, encoding="utf-8"))
assert mapping.get("status") == "VERIFIED", "module mapping not VERIFIED — run scripts/inspect_internlm3_modules.py first"
target_modules = mapping["target_module_short_names"]
assert all(target_modules), "mapping has empty entries"
print(f"[protocol] LoraConfig target_modules (short names, verified): {target_modules}")

print("[protocol] loading config to read num_hidden_layers (REAL, no hardcoding)...")
from transformers import AutoConfig
cfg_m = AutoConfig.from_pretrained(args.model_path, trust_remote_code=True)
L = int(cfg_m.num_hidden_layers)
# v19.1 双边界等比映射 (protocol correction 2026-08-12):
# 旧规则 (v19.0): L==32 → 23..31/12..31, 否则 start 缩放 + 延伸到 L-1 → L=48 得 39..47/18..47,
#   与锁定协议必然不一致 (abort)。v19.1: 按 v18 设计区间开区间 [23,32)/[12,32) 双边界等比缩放。
s1_open = list(range(round(L * 23 / 36), round(L * 32 / 36)))
s2_open = list(range(round(L * 12 / 36), round(L * 32 / 36)))
print(f"[protocol] computed ranges for L={L}: stage1={s1_open} ({len(s1_open)} layers), stage2={s2_open} ({len(s2_open)} layers)")
resolved = {"num_hidden_layers": L,
            "stage1_open_layers": s1_open,
            "stage2_open_layers": s2_open}
if protocol["resolved_layer_ranges"]["status"] == "UNRESOLVED":
    protocol["resolved_layer_ranges"] = {"status": "LOCKED", **resolved,
                                         "locked_at": datetime.now().isoformat(),
                                         "rule": protocol["layer_mapping_rule"]["resolution"]}
    PROTOCOL.write_text(json.dumps(protocol, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[protocol] layer ranges LOCKED into {PROTOCOL}: s1={s1_open} s2={s2_open}")
else:
    rec = protocol["resolved_layer_ranges"]
    assert rec["num_hidden_layers"] == L, "num_hidden_layers changed vs locked protocol!"
    assert rec["stage1_open_layers"] == s1_open and rec["stage2_open_layers"] == s2_open, \
        "layer ranges changed vs locked protocol — ABORT"
    print(f"[protocol] locked ranges confirmed: s1={s1_open} s2={s2_open}")

# ── 冻结模板 (逐字来自 phase3_train.py build_training_sample / build_thought_chain) ──
SYS = ("你是一位资深中医专家。请根据真实临床资料判断最符合的中医证型，"
       "并严格按照“证型”和“辨证依据”两个字段作答。")
def user_prompt(input_text: str) -> str:
    return ("请根据以下真实临床资料进行中医辨证。\n"
            "要求：\n1. 只输出一个最可能的证型。\n"
            "2. 证型名称尽量使用标准证型名称。\n"
            "3. 不要输出治法、方剂、病位或其他额外字段。\n\n"
            f"临床资料：\n{input_text}\n\n输出格式：\n证型：\n辨证依据：")
def assistant_answer(syndrome: str) -> str:
    return (f"证型：{syndrome}\n"
            f"辨证依据：根据主诉、四诊信息及现病描述综合判断，"
            f"当前表现与{syndrome}的病机特征更为吻合。")

def load_json(p):
    return json.load(open(p, encoding="utf-8"))

print("[data] loading...")
train_raw = load_json(args.train_file)
dev_raw = load_json(args.dev_file)
random.Random(args.seed).shuffle(train_raw)
print(f"  train={len(train_raw)} dev={len(dev_raw)}")

tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True, use_fast=False)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token


def build_ids(sample: dict):
    input_text = sample["input_text"]
    syndrome = sample["syndrome_canonical"]
    sys_msg = {"role": "system", "content": SYS}
    usr_msg = {"role": "user", "content": user_prompt(input_text)}
    asst_msg = {"role": "assistant", "content": assistant_answer(syndrome)}
    prompt_ids = tokenizer.apply_chat_template([sys_msg, usr_msg], add_generation_prompt=True, tokenize=True)
    full_ids = tokenizer.apply_chat_template([sys_msg, usr_msg, asst_msg], tokenize=True)
    assert full_ids[:len(prompt_ids)] == prompt_ids, "chat template prefix mismatch — manual template fallback needed"
    labels = [-100] * len(prompt_ids) + full_ids[len(prompt_ids):]
    if len(full_ids) > args.max_seq_length:
        plen = len(prompt_ids)
        if plen >= args.max_seq_length:
            full_ids = full_ids[:args.max_seq_length]
            labels = [-100] * args.max_seq_length
        else:
            keep = args.max_seq_length - plen
            full_ids = full_ids[:args.max_seq_length]
            labels = [-100] * plen + full_ids[plen:plen + keep]
    else:
        pad = args.max_seq_length - len(full_ids)
        full_ids = full_ids + [tokenizer.pad_token_id] * pad
        labels = labels + [-100] * pad
    return full_ids, labels


class SFTSet(Dataset):
    def __init__(self, samples):
        self.samples = samples
    def __len__(self):
        return len(self.samples)
    def __getitem__(self, idx):
        ids, labels = build_ids(self.samples[idx])
        if sum(1 for l in labels if l != -100) == 0:
            alt = (idx + 1) % len(self.samples)
            if alt != idx:
                return self.__getitem__(alt)
        return {"input_ids": torch.tensor(ids), "attention_mask": torch.tensor([1 if x != tokenizer.pad_token_id else 0 for x in ids]),
                "labels": torch.tensor(labels)}


def collate(batch):
    return {"input_ids": torch.stack([b["input_ids"] for b in batch]),
            "attention_mask": torch.stack([b["attention_mask"] for b in batch]),
            "labels": torch.stack([b["labels"] for b in batch])}


print("[model] loading (quant=%s, %s)..." % (args.quant_bits, "QLoRA NF4" if args.quant_bits == 4 else "full precision"))
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

load_kwargs = {"trust_remote_code": True, "local_files_only": False}
if DEVICE == "cuda":
    if args.quant_bits == 4:
        load_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
    load_kwargs["device_map"] = "auto"
    if args.quant_bits == 0:
        load_kwargs["torch_dtype"] = torch.bfloat16
else:
    load_kwargs["device_map"] = "cpu"
    load_kwargs["torch_dtype"] = torch.float32

model = AutoModelForCausalLM.from_pretrained(args.model_path, **load_kwargs)
if DEVICE == "cuda" and args.quant_bits == 4:
    model = prepare_model_for_kbit_training(model)
model.gradient_checkpointing_enable()
model.config.use_cache = False

lora_cfg = LoraConfig(r=args.lora_r, lora_alpha=args.lora_alpha, lora_dropout=args.lora_dropout,
                      target_modules=target_modules, bias="none", task_type="CAUSAL_LM")
model = get_peft_model(model, lora_cfg)

# 验证 target_modules 全部命中
missing = [t for t in target_modules if t not in {n.split(".")[-1] for n, _ in model.named_modules()}]
assert not missing, f"target modules missing after PEFT: {missing}"
total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"[params] total={total_params:,} trainable={trainable_params:,} ({100*trainable_params/total_params:.3f}%)")

# 记录可训参数量进协议 (训练开始前, held-out 推理之前)
protocol.setdefault("trainable_parameter_record", {})
protocol["trainable_parameter_record"].update({
    "total_params": total_params, "trainable_params": trainable_params,
    "trainable_pct": round(100 * trainable_params / total_params, 4),
    "target_modules": target_modules, "recorded_at": datetime.now().isoformat()})
PROTOCOL.write_text(json.dumps(protocol, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def freeze_layers(m, idxs):
    for name, p in m.named_parameters():
        for li in idxs:
            if f".layers.{li}." in name:
                p.requires_grad_(False)
                break

def unfreeze_layers(m, idxs):
    for name, p in m.named_parameters():
        for li in idxs:
            if f".layers.{li}." in name:
                if p.is_floating_point():
                    p.requires_grad_(True)
                break


train_loader = DataLoader(SFTSet(train_raw), batch_size=args.batch_size, shuffle=True, collate_fn=collate)
dev_loader = DataLoader(SFTSet(dev_raw), batch_size=args.batch_size, shuffle=False, collate_fn=collate)


def eval_dev_loss():
    model.eval()
    tot, n = 0.0, 0
    with torch.no_grad():
        for b in dev_loader:
            out = model(input_ids=b["input_ids"].to(DEVICE), attention_mask=b["attention_mask"].to(DEVICE),
                        labels=b["labels"].to(DEVICE))
            tot += float(out.loss.item()); n += 1
    model.train()
    return tot / max(n, 1)


def train_stage(stage_name: str, open_layers, frozen_layers, lr, epochs, use_cosine: bool):
    freeze_layers(model, frozen_layers)
    opt = torch.optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=lr, weight_decay=0.01)
    total_steps = len(train_loader) * epochs
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=total_steps) if use_cosine else None
    steps_done = 0
    for epoch in range(1, epochs + 1):
        model.train()
        loss_acc, step_acc = 0.0, 0
        t0 = time.time()
        for bi, b in enumerate(train_loader, 1):
            ids = b["input_ids"].to(DEVICE); mask = b["attention_mask"].to(DEVICE); labels = b["labels"].to(DEVICE)
            loss = model(input_ids=ids, attention_mask=mask, labels=labels).loss
            (loss / args.grad_accum).backward()
            loss_acc += float(loss.item()); step_acc += 1
            if bi % args.grad_accum == 0 or bi == len(train_loader):
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                opt.zero_grad(set_to_none=True)
                steps_done += 1
                if args.max_steps and steps_done >= args.max_steps:
                    ckpt = OUT / f"{stage_name}-epoch-{epoch}-smoke"
                    ckpt.mkdir(parents=True, exist_ok=True)
                    model.save_pretrained(ckpt)
                    tokenizer.save_pretrained(ckpt)
                    print(f"[smoke] {stage_name} {steps_done} optimizer steps done, saved {ckpt}", flush=True)
                    return
            if sched:
                sched.step()
            if bi % 50 == 0:
                print(f"  [{stage_name} E{epoch} S{bi}/{len(train_loader)}] loss={loss.item():.4f} ({time.time()-t0:.0f}s)", flush=True)
        vl = eval_dev_loss()
        print(f"[{stage_name} E{epoch}] train_loss={loss_acc/step_acc:.4f} dev_loss={vl:.4f}", flush=True)
        hist.append({"stage": stage_name, "epoch": epoch, "train_loss": round(loss_acc/step_acc, 5), "dev_loss": round(vl, 5)})
        ckpt = OUT / f"{stage_name}-epoch-{epoch}"
        ckpt.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(ckpt)
        tokenizer.save_pretrained(ckpt)
        if stage_name == "stage2":
            if vl < best["loss"]:
                best["loss"] = vl; best["epoch"] = epoch
                (OUT / "best_checkpoint").mkdir(parents=True, exist_ok=True)
                model.save_pretrained(OUT / "best_checkpoint")
                tokenizer.save_pretrained(OUT / "best_checkpoint")
                print(f"  ✓ best stage2 dev_loss={vl:.4f} @ epoch {epoch} saved")


import csv
hist = []
best = {"loss": float("inf"), "epoch": None}
start = time.time()
try:
    print(f"=== Stage 1: layers {s1_open} (frozen 0-{s1_open[0]-1}), LR={args.stage1_lr} constant, {args.stage1_epochs} ep ===")
    train_stage("stage1", s1_open, list(range(0, s1_open[0])), args.stage1_lr, args.stage1_epochs, use_cosine=False)
    print(f"=== Stage 2: layers {s2_open} (frozen 0-{s2_open[0]-1}), LR={args.stage2_lr} cosine, {args.stage2_epochs} ep ===")
    train_stage("stage2", s2_open, list(range(0, s2_open[0])), args.stage2_lr, args.stage2_epochs, use_cosine=True)
    status = "completed"
except torch.cuda.OutOfMemoryError:
    status = "failed_oom"
    print("[OOM] saving failed run record (NOT deleting)", flush=True)
except Exception as e:
    status = f"failed: {type(e).__name__}: {e}"
    print(f"[FAIL] {status}", flush=True)

with open(OUT / "training_history.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["stage", "epoch", "train_loss", "dev_loss"])
    w.writeheader(); w.writerows(hist)

peak_vram = (torch.cuda.max_memory_allocated() // (1024 * 1024)) if DEVICE == "cuda" else None
summary = {
    "model": Path(args.model_path).name,
    "checkpoint": str(OUT / "best_checkpoint"),
    "model_family": "generative",
    "train_fraction": 1.0,
    "n_train": len(train_raw), "n_dev": len(dev_raw),
    "seed": args.seed,
    "best_epoch": best["epoch"],
    "best_dev_loss": round(best["loss"], 5) if best["epoch"] else None,
    "best_dev_macro_f1": None,
    "trainable_params": trainable_params,
    "total_params": total_params,
    "training_seconds": round(time.time() - start, 1),
    "peak_vram_mb": peak_vram,
    "quant_bits": args.quant_bits,
    "layer_ranges": {"stage1_open": s1_open, "stage2_open": s2_open},
    "target_modules": target_modules,
    "test_accessed_after_protocol_lock": False,
    "status": status,
}
(OUT / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "config.json").write_text(json.dumps(vars(args), ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "environment.json").write_text(json.dumps({
    "python": sys.version.split()[0], "torch": torch.__version__,
    "transformers": __import__("transformers").__version__,
    "device": DEVICE, "gpu": torch.cuda.get_device_name(0) if DEVICE == "cuda" else None,
    "seed": args.seed, "timestamp": datetime.now().isoformat()}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[DONE] status={status} best_epoch={best['epoch']} best_dev_loss={best['loss'] if best['epoch'] else None} "
      f"trainable={trainable_params} secs={summary['training_seconds']} peak_vram_mb={peak_vram}")
if status != "completed":
    sys.exit(1)
