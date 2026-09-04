#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
train_encoder.py — v19 通用 encoder 训练器 (MacBERT 协议泛化)
=============================================================
由 v18 冻结脚本 extra_experiments/runs/t1_macbert/t1_macbert.py 泛化而来，
训练动态逐行保持一致 (AdamW 双组 / 线性 warmup / FP16 scaler / clip 1.0 /
dev macro-F1 早停 patience=3)。ZY-BERT 主实验超参与 MacBERT 完全一致。

用法:
  python scripts/train_encoder.py \
      --model-path <zybert官方checkpoint目录> \
      --train-file ../../../v18_working/dataset_audit/data/train_4186.json \
      --dev-file   ../../../v18_working/dataset_audit/data/dev_420.json \
      --labels-file ../../../v18_working/evaluation/labels_42.txt \
      --output-dir runs/zybert/full/seed42 \
      --seed 42

纪律:
  - checkpoint 只按 dev macro-F1 选择; held-out 在整个训练期间绝不接触。
  - 输入只取 item["input_text"], 标签只取 item["syndrome_canonical"]。
  - 模型加载 local_files_only=True (AutoDL 国内节点无 HF 直连)。
"""
import argparse
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoConfig,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)

LOCAL_EVAL = Path(__file__).resolve().parent
sys.path.insert(0, str(LOCAL_EVAL))
from evaluate import compute_metrics  # noqa: E402  (v18 冻结 evaluator)

parser = argparse.ArgumentParser()
parser.add_argument("--model-path", required=True, help="pretrained encoder dir (local, official checkpoint)")
parser.add_argument("--train-file", required=True)
parser.add_argument("--dev-file", required=True)
parser.add_argument("--labels-file", required=True, help="labels_42.txt (order frozen, do not reorder)")
parser.add_argument("--output-dir", required=True)
parser.add_argument("--max-length", type=int, default=512)
parser.add_argument("--batch-size", type=int, default=16)
parser.add_argument("--lr", type=float, default=2e-5)
parser.add_argument("--weight-decay", type=float, default=0.01)
parser.add_argument("--warmup-ratio", type=float, default=0.1)
parser.add_argument("--num-epochs", type=int, default=10)
parser.add_argument("--patience", type=int, default=3)
parser.add_argument("--seed", type=int, default=42)
parser.add_argument("--dropout", type=float, default=0.1)
parser.add_argument("--fp16", action="store_true", default=True)
parser.add_argument("--no-fp16", action="store_false", dest="fp16")
parser.add_argument("--model-name-for-env", default=None, help="registry id e.g. zybert / macbert")
args = parser.parse_args()

OUT = Path(args.output_dir)
OUT.mkdir(parents=True, exist_ok=True)
MODEL_DIR = OUT / "best_checkpoint"

# ── seed ──
random.seed(args.seed)
np.random.seed(args.seed)
torch.manual_seed(args.seed)
torch.cuda.manual_seed_all(args.seed)

# ── device ──
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[device] {DEVICE} {torch.cuda.get_device_name(0) if DEVICE.type=='cuda' else '(CPU)'}")

# ── labels (frozen order) ──
LABELS = [l.strip() for l in open(args.labels_file, encoding="utf-8") if l.strip()]
assert len(LABELS) == 42, f"labels != 42: {len(LABELS)}"
label2id = {l: i for i, l in enumerate(LABELS)}
id2label = {i: l for i, l in enumerate(LABELS)}
print(f"[labels] {len(LABELS)} classes (order frozen from labels_42.txt)")


def load_json(p: Path) -> list:
    return json.load(open(p, encoding="utf-8"))


def build_input_text(item: dict) -> str:
    """input_text 优先; 缺失时按冻结拼接 (仅 fallback, 数据应已含 input_text)."""
    if item.get("input_text"):
        return item["input_text"]
    parts = []
    if item.get("lcd_name"):
        parts.append(f"疾病名称：{item['lcd_name']}")
    if item.get("chief_complaint"):
        parts.append(f"主诉：{item['chief_complaint']}")
    if item.get("detection"):
        parts.append(f"四诊信息：{item['detection']}")
    if item.get("description"):
        parts.append(f"现病描述摘要：{item['description']}")
    return "\n".join(parts)


class TCMDataset(Dataset):
    def __init__(self, data, tokenizer, max_length):
        self.data, self.tokenizer, self.max_length = data, tokenizer, max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        text = build_input_text(item)
        enc = self.tokenizer(text, truncation=True, max_length=self.max_length,
                             padding="max_length", return_tensors="pt")
        lab = label2id.get(item.get("syndrome_canonical", ""), -1)
        if lab == -1:
            raise ValueError(f"unknown label {item.get('syndrome_canonical')} id={item.get('id')}")
        return {"input_ids": enc["input_ids"].squeeze(0),
                "attention_mask": enc["attention_mask"].squeeze(0),
                "label": torch.tensor(lab, dtype=torch.long),
                "idx": idx}


def evaluate(model, loader):
    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for b in loader:
            logits = model(input_ids=b["input_ids"].to(DEVICE),
                           attention_mask=b["attention_mask"].to(DEVICE)).logits
            preds = torch.argmax(logits, dim=-1)
            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(b["label"].cpu().tolist())
    return compute_metrics([id2label[l] for l in all_labels],
                           [id2label[p] for p in all_preds])


def main():
    start = time.time()
    train_data = load_json(args.train_file)
    dev_data = load_json(args.dev_file)
    print(f"[data] train={len(train_data)} dev={len(dev_data)}")

    try:
        tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True)
    except Exception:
        print("[adapt] AutoTokenizer failed; retrying with explicit BertTokenizer (official old-format checkpoint)")
        from transformers import BertTokenizer
        tokenizer = BertTokenizer.from_pretrained(args.model_path, local_files_only=True)
    train_ds = TCMDataset(train_data, tokenizer, args.max_length)
    dev_ds = TCMDataset(dev_data, tokenizer, args.max_length)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    dev_loader = DataLoader(dev_ds, batch_size=args.batch_size, shuffle=False)

    config = AutoConfig.from_pretrained(
        args.model_path, num_labels=len(LABELS),
        hidden_dropout_prob=args.dropout,
        attention_probs_dropout_prob=args.dropout,
        classifier_dropout=args.dropout,
        local_files_only=True)
    try:
        model = AutoModelForSequenceClassification.from_pretrained(
            args.model_path, config=config, local_files_only=True)
    except Exception as e:
        # 官方旧格式适配 (ZY-BERT: transformers 2.3.0 时代 checkpoint, config 可能缺 model_type)
        print(f"[adapt] AutoModelForSequenceClassification failed ({e}); retrying with explicit BertConfig/BertForSequenceClassification (same official checkpoint)")
        from transformers import BertConfig as _BC, BertForSequenceClassification as _BFSC
        config_bert = _BC.from_pretrained(args.model_path, num_labels=len(LABELS),
                                          hidden_dropout_prob=args.dropout,
                                          attention_probs_dropout_prob=args.dropout,
                                          classifier_dropout=args.dropout,
                                          local_files_only=True)
        model = _BFSC.from_pretrained(args.model_path, config=config_bert, local_files_only=True)
    model.to(DEVICE)

    no_decay = ["bias", "LayerNorm.weight"]
    opt_groups = [
        {"params": [p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)],
         "weight_decay": args.weight_decay},
        {"params": [p for n, p in model.named_parameters() if any(nd in n for nd in no_decay)],
         "weight_decay": 0.0},
    ]
    optimizer = AdamW(opt_groups, lr=args.lr)
    total_steps = len(train_loader) * args.num_epochs
    warmup_steps = int(total_steps * args.warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_steps)
    scaler = torch.cuda.amp.GradScaler() if args.fp16 and DEVICE.type == "cuda" else None

    best_dev_f1, best_epoch, patience_counter = -1.0, -1, 0
    history = []
    dev_preds_records = []

    for epoch in range(1, args.num_epochs + 1):
        model.train()
        total_loss, ep_start = 0.0, time.time()
        for bi, b in enumerate(train_loader):
            ids = b["input_ids"].to(DEVICE)
            mask = b["attention_mask"].to(DEVICE)
            labels = b["label"].to(DEVICE)
            optimizer.zero_grad()
            if scaler:
                with torch.cuda.amp.autocast():
                    loss = model(input_ids=ids, attention_mask=mask, labels=labels).loss
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
            else:
                loss = model(input_ids=ids, attention_mask=mask, labels=labels).loss
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
            scheduler.step()
            total_loss += loss.item()
        avg_loss = total_loss / len(train_loader)

        m = evaluate(model, dev_loader)
        dev_f1 = m["macro_f1"]
        history.append({"epoch": epoch, "train_loss": round(avg_loss, 5),
                        "dev_acc": round(m["syn_acc@1"], 5), "dev_macro_f1": round(dev_f1, 5)})
        print(f"[E{epoch}] loss={avg_loss:.4f} dev_acc={m['syn_acc@1']:.4f} dev_macroF1={dev_f1:.4f} "
              f"({time.time()-ep_start:.0f}s)", flush=True)
        if dev_f1 > best_dev_f1:
            best_dev_f1, best_epoch, patience_counter = dev_f1, epoch, 0
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(MODEL_DIR)
            tokenizer.save_pretrained(MODEL_DIR)
            print(f"  ✓ best @ epoch {epoch} saved")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"[early stop] @ epoch {epoch}")
                break

    # ── dev predictions from best checkpoint ──
    best = AutoModelForSequenceClassification.from_pretrained(
        MODEL_DIR, local_files_only=True).to(DEVICE)
    best.eval()
    with torch.no_grad():
        for i, b in enumerate(dev_loader):
            logits = best(input_ids=b["input_ids"].to(DEVICE),
                          attention_mask=b["attention_mask"].to(DEVICE)).logits
            probs = torch.softmax(logits, dim=-1)
            for j, idx in enumerate(b["idx"].tolist()):
                pv = probs[j]
                top3 = torch.topk(pv, k=min(3, len(LABELS)))
                rec = {"id": dev_data[idx]["id"],
                       "gold": dev_data[idx]["syndrome_canonical"],
                       "pred": id2label[int(torch.argmax(logits[j]))],
                       "confidence": round(float(pv.max()), 4),
                       "top3_labels": [id2label[int(t)] for t in top3.indices.tolist()],
                       "top3_probs": [round(float(x), 4) for x in top3.values.tolist()]}
                dev_preds_records.append(rec)
    (OUT / "dev_predictions.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in dev_preds_records) + "\n", encoding="utf-8")

    # ── artifacts ──
    import csv
    with open(OUT / "training_history.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["epoch", "train_loss", "dev_acc", "dev_macro_f1"])
        w.writeheader(); w.writerows(history)

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    peak_vram = (torch.cuda.max_memory_allocated() // (1024 * 1024)) if DEVICE.type == "cuda" else None

    cfg_out = {
        "model_path": args.model_path, "task": "42-class sequence classification",
        "input": "item['input_text']", "target": "item['syndrome_canonical']",
        "max_length": args.max_length, "batch_size": args.batch_size, "lr": args.lr,
        "weight_decay": args.weight_decay, "warmup_ratio": args.warmup_ratio,
        "num_epochs": args.num_epochs, "patience": args.patience, "seed": args.seed,
        "dropout": args.dropout, "fp16": bool(scaler), "early_stopping": "dev macro-F1",
    }
    env_out = {
        "python": sys.version.split()[0], "torch": torch.__version__,
        "device": str(DEVICE), "gpu_name": torch.cuda.get_device_name(0) if DEVICE.type == "cuda" else None,
        "transformers": __import__("transformers").__version__,
        "seed": args.seed, "timestamp": datetime.now().isoformat(),
    }
    summary = {
        "model": args.model_name_for_env or Path(args.model_path).name,
        "checkpoint": str(MODEL_DIR),
        "model_family": "discriminative",
        "train_fraction": 1.0,
        "n_train": len(train_data), "n_dev": len(dev_data),
        "seed": args.seed,
        "best_epoch": best_epoch,
        "best_dev_macro_f1": round(best_dev_f1, 5),
        "trainable_params": trainable_params,
        "total_params": total_params,
        "training_seconds": round(time.time() - start, 1),
        "peak_vram_mb": peak_vram,
        "test_accessed_after_protocol_lock": False,  # held-out never touched
        "status": "completed",
    }
    (OUT / "config.json").write_text(json.dumps(cfg_out, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "environment.json").write_text(json.dumps(env_out, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[DONE] best_epoch={best_epoch} best_dev_macroF1={best_dev_f1:.4f} "
          f"trainable={trainable_params} total={total_params} secs={summary['training_seconds']}")


if __name__ == "__main__":
    main()
