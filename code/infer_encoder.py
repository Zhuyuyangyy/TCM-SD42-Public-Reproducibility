#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
infer_encoder.py — v19 encoder 推理 (协议锁定后一次性执行)
=========================================================
用法:
  python scripts/infer_encoder.py \
      --checkpoint runs/zybert/full/seed42/best_checkpoint \
      --labels-file ../../../v18_working/evaluation/labels_42.txt \
      --test-file ../../../v18_working/dataset_audit/data/pilot_test_420.json \
      --output predictions/zybert/full/seed42/pilot420.jsonl

输出 JSONL (每行):
  {"id","gold","pred","confidence","top3_labels","top3_probs"}
顺序 = 测试文件顺序 (供后续按 id 过滤 clean 集)。
"""
import argparse
import json
import sys
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

LOCAL_EVAL = Path(__file__).resolve().parent
sys.path.insert(0, str(LOCAL_EVAL))
from evaluate import compute_metrics  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("--checkpoint", required=True)
parser.add_argument("--labels-file", required=True)
parser.add_argument("--test-file", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--batch-size", type=int, default=64)
parser.add_argument("--max-length", type=int, default=512)
args = parser.parse_args()

LABELS = [l.strip() for l in open(args.labels_file, encoding="utf-8") if l.strip()]
id2label = {i: l for i, l in enumerate(LABELS)}
label2id = {l: i for i, l in enumerate(LABELS)}
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

data = json.load(open(args.test_file, encoding="utf-8"))
tok = AutoTokenizer.from_pretrained(args.checkpoint, local_files_only=True)
model = AutoModelForSequenceClassification.from_pretrained(args.checkpoint, local_files_only=True).to(DEVICE)
model.eval()
print(f"[infer] n={len(data)} device={DEVICE}")

records = []
with torch.no_grad():
    for i in range(0, len(data), args.batch_size):
        batch = data[i:i + args.batch_size]
        texts = [it["input_text"] if it.get("input_text") else "" for it in batch]
        enc = tok(texts, truncation=True, max_length=args.max_length,
                  padding="max_length", return_tensors="pt").to(DEVICE)
        logits = model(**enc).logits
        probs = torch.softmax(logits, dim=-1)
        for j, it in enumerate(batch):
            pv = probs[j]
            top3 = torch.topk(pv, k=min(3, len(LABELS)))
            records.append({
                "id": it["id"],
                "gold": it["syndrome_canonical"],
                "pred": id2label[int(torch.argmax(logits[j]))],
                "confidence": round(float(pv.max()), 4),
                "top3_labels": [id2label[int(t)] for t in top3.indices.tolist()],
                "top3_probs": [round(float(x), 4) for x in top3.values.tolist()],
            })

out = Path(args.output)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8")
m = compute_metrics([r["gold"] for r in records], [r["pred"] for r in records])
print(f"[metrics] n={m['n']} syn@1={m['syn_acc@1']:.4f} macroF1={m['macro_f1']:.4f} "
      f"balAcc={m['balanced_accuracy']:.4f} fmt={m['format_validity']:.4f} empty={m['empty_pred_rate']:.4f}")
print(f"[saved] {out}")
