#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_four_model_clean4218.py — 生成四模型 clean4218 逐例对齐文件 (seed42)
输出:
  predictions/four_model_clean4218_seed42.jsonl  (id, gold, 四模型 pred)
  predictions/four_model_clean4218_seed42.csv    (同内容, 带表头)
对齐口径与 tables/full_data_seed42.csv / make_four_model_report.py 完全一致:
  - ZY-BERT / InternLM3: id 直连 (heldout4452.jsonl, SEAL 已验)
  - MacBERT / Qwen3: v18 冻结预测按 full_test_4452.json 位置 ↔ clean id 过滤
"""
import argparse, csv, json
from pathlib import Path

ap = argparse.ArgumentParser(description="Build the clean4218 four-model alignment file from frozen local evidence.")
ap.add_argument("--v20-package", type=Path, required=True,
                 help="Path to the unpacked v20 evidence package.")
ap.add_argument("--v18-root", type=Path, required=True,
                 help="Path to the unpacked v18 working evidence tree.")
ap.add_argument("--output-dir", type=Path, default=Path("predictions"),
                 help="Directory for the generated alignment files.")
args = ap.parse_args()
PKG = args.v20_package
V18 = args.v18_root
OUT_DIR = args.output_dir

def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]

CLEAN = json.load(open(PKG / "data/heldout_clean_4218.json", encoding="utf-8"))
clean_ids = [it["id"] for it in CLEAN]
gold_by_id = {it["id"]: it["syndrome_canonical"] for it in CLEAN}

FULL_4452 = json.load(open(V18 / "dataset_audit/data/full_test_4452.json", encoding="utf-8"))
pos_of_id = {it["id"]: i for i, it in enumerate(FULL_4452)}

def v18_clean(p):
    preds = load_jsonl(p)
    return {cid: preds[pos_of_id[cid]]["pred"] for cid in clean_ids}

def v19_clean(p):
    pmap = {x["id"]: x for x in load_jsonl(p)}
    return {cid: pmap[cid]["pred"] for cid in clean_ids}

M = {
    "macbert":   v18_clean(PKG / "predictions/v18_models/macbert_heldout4452.jsonl"),
    "qwen3":     v18_clean(PKG / "predictions/v18_models/qwen3_sft_clean_v3_heldout4452.jsonl"),
    "zybert":    v19_clean(PKG / "predictions/zybert/full/seed42/heldout4452.jsonl"),
    "internlm3": v19_clean(PKG / "predictions/internlm3/full/seed42/heldout4452.jsonl"),
}

# 输出只写到 --output-dir (绝不写回冻结源)
out = OUT_DIR
out.mkdir(parents=True, exist_ok=True)
with open(out / "four_model_clean4218_seed42.jsonl", "w", encoding="utf-8") as f:
    for cid in clean_ids:
        rec = {"id": cid, "gold": gold_by_id[cid]}
        rec.update({k: M[k][cid] for k in M})
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

with open(out / "four_model_clean4218_seed42.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "gold"] + list(M))
    for cid in clean_ids:
        w.writerow([cid, gold_by_id[cid]] + [M[k][cid] for k in M])

print(f"written: {out/'four_model_clean4218_seed42.jsonl'} ({len(clean_ids)} rows)")
print(f"written: {out/'four_model_clean4218_seed42.csv'}")
