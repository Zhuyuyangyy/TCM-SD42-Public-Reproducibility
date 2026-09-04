#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
infer_llm.py — v19 LLM 推理 (确定性, 协议锁定后一次性执行)
=========================================================
口径 (与 Qwen3 SFT 对齐):
  - do_sample=False, temperature=0, max_new_tokens=96
  - 系统任务语义与 Qwen3 冻结任务一致 (证型+辨证依据), 经模型原生 chat template
  - 先保存 raw JSONL {id, gold_syndrome, raw_output}
  - 再用 v18 统一 evaluation/parse_label.py 解析 → {id, gold, pred}
    (禁止为 InternLM3 写更宽松 parser)

用法:
  python scripts/infer_llm.py \
      --checkpoint runs/internlm3/full/seed42/best_checkpoint \
      --base-model internlm/internlm3-8b-instruct \
      --test-file ../../../v18_working/dataset_audit/data/full_test_4452.json \
      --output-raw predictions/internlm3/full/seed42/heldout4452_raw.jsonl \
      --output-parsed predictions/internlm3/full/seed42/heldout4452.jsonl
"""
import argparse
import json
import sys
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

LOCAL_EVAL = Path(__file__).resolve().parent
sys.path.insert(0, str(LOCAL_EVAL))
from parse_label import parse_label_from_output  # noqa: E402  (v18 冻结 parser, 唯一)
from evaluate import compute_metrics  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("--checkpoint", required=True)
parser.add_argument("--base-model", required=True)
parser.add_argument("--test-file", required=True)
parser.add_argument("--output-raw", required=True)
parser.add_argument("--output-parsed", required=True)
parser.add_argument("--max-new-tokens", type=int, default=96)
parser.add_argument("--batch-size", type=int, default=1)
parser.add_argument("--quant-bits", type=int, default=4)
parser.add_argument("--save-token-ids", action="store_true",
                    help="raw record 追加 new_tokens (generated token IDs) 字段, 用于 batch-size 一致性对照")
args = parser.parse_args()

SYS = ("你是一位资深中医专家。请根据真实临床资料判断最符合的中医证型，"
       "并严格按照“证型”和“辨证依据”两个字段作答。")
def user_prompt(input_text: str) -> str:
    return ("请根据以下真实临床资料进行中医辨证。\n"
            "要求：\n1. 只输出一个最可能的证型。\n"
            "2. 证型名称尽量使用标准证型名称。\n"
            "3. 不要输出治法、方剂、病位或其他额外字段。\n\n"
            f"临床资料：\n{input_text}\n\n输出格式：\n证型：\n辨证依据：")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[infer] device={DEVICE}")

print("[load] base + adapter...")
load_kwargs = {"trust_remote_code": True, "local_files_only": False}
if DEVICE == "cuda" and args.quant_bits == 4:
    load_kwargs["quantization_config"] = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)
    load_kwargs["device_map"] = "auto"
elif DEVICE == "cuda":
    load_kwargs["device_map"] = "auto"
    load_kwargs["torch_dtype"] = torch.bfloat16
else:
    load_kwargs["device_map"] = "cpu"
    load_kwargs["torch_dtype"] = torch.float32

model = AutoModelForCausalLM.from_pretrained(args.base_model, **load_kwargs)
model = PeftModel.from_pretrained(model, args.checkpoint)
model.eval()
tok = AutoTokenizer.from_pretrained(args.checkpoint, trust_remote_code=True, use_fast=False)

data = json.load(open(args.test_file, encoding="utf-8"))
print(f"[infer] n={len(data)}")

raw_records, parsed_records = [], []
B = max(1, args.batch_size)
# 与训练脚本口径一致: pad_token 缺失时 pad = eos (InternLM3 tokenizer)
pad_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
eos_id = tok.eos_token_id
if tok.pad_token_id is None:
    tok.pad_token_id = pad_id
print(f"[infer] batch_size={B} (real batching, left-pad + explicit attention_mask)")
with torch.no_grad():
    for start in range(0, len(data), B):
        chunk = data[start:start + B]
        ids_list = []
        for it in chunk:
            messages = [{"role": "system", "content": SYS},
                        {"role": "user", "content": user_prompt(it["input_text"])}]
            ids = tok.apply_chat_template(messages, add_generation_prompt=True, tokenize=True)
            ids_list.append(ids)
        maxlen = max(len(x) for x in ids_list)
        padded = torch.full((len(chunk), maxlen), pad_id, dtype=torch.long)
        mask = torch.zeros((len(chunk), maxlen), dtype=torch.long)
        for j, ids in enumerate(ids_list):
            off = maxlen - len(ids)
            padded[j, off:] = torch.tensor(ids)
            mask[j, off:] = 1
        out = model.generate(input_ids=padded.to(DEVICE), attention_mask=mask.to(DEVICE),
                             do_sample=False, temperature=0.0,
                             max_new_tokens=args.max_new_tokens,
                             pad_token_id=pad_id, eos_token_id=eos_id)
        for j, it in enumerate(chunk):
            new_tokens = out[j, maxlen:].tolist()
            # 统一截断到第一个 eos (pad==eos: batch 填充与停止信号同 token, 必须与 batch=1 同口径)
            if eos_id in new_tokens:
                new_tokens = new_tokens[:new_tokens.index(eos_id) + 1]
            raw = tok.decode(new_tokens, skip_special_tokens=True)
            rec = {"id": it["id"], "gold_syndrome": it["syndrome_canonical"], "raw_output": raw}
            if args.save_token_ids:
                rec["new_tokens"] = new_tokens
            raw_records.append(rec)
            pred = parse_label_from_output(raw)
            parsed_records.append({"id": it["id"], "gold": it["syndrome_canonical"], "pred": pred, "confidence": None})
        done = min(start + B, len(data))
        if done % 100 == 0 or done == len(data):
            print(f"  {done}/{len(data)}", flush=True)

raw_out = Path(args.output_raw); raw_out.parent.mkdir(parents=True, exist_ok=True)
raw_out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in raw_records) + "\n", encoding="utf-8")
parsed_out = Path(args.output_parsed); parsed_out.parent.mkdir(parents=True, exist_ok=True)
parsed_out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in parsed_records) + "\n", encoding="utf-8")

m = compute_metrics([r["gold"] for r in parsed_records], [r["pred"] for r in parsed_records])
print(f"[metrics] n={m['n']} syn@1={m['syn_acc@1']:.4f} macroF1={m['macro_f1']:.4f} "
      f"balAcc={m['balanced_accuracy']:.4f} fmt={m['format_validity']:.4f} empty={m['empty_pred_rate']:.4f}")
print(f"[saved] {raw_out}\n[saved] {parsed_out}")
