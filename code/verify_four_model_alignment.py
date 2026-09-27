#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_four_model_alignment.py — addendum 版反向验证脚本 (v23 stats addendum)

职责:
  1. 读取 predictions/four_model_clean4218_seed42.jsonl (唯一输入)
  2. 校验: 4218 行 / id 唯一 / id 顺序与 gold 与 v20 冻结 heldout_clean_4218.json 一致
  3. 用冻结 42 类 label list (data_documentation/labels_42.txt, 内嵌副本) +
     sklearn 权威口径重算四模型 Accuracy / Macro-F1 / Weighted-F1 / Balanced Accuracy
  4. 与冻结 tables/full_data_seed42.csv 对照, 容差 5e-5 (舍入级)
     — 任一模型任一指标超差即 FAIL, 退出码 1 (反向验证 gate)

用法:
  python3 evaluation/verify_four_model_alignment.py [--root DIR] [--frozen-csv PATH]
"""
import argparse
import csv
import json
import sys
from pathlib import Path

from sklearn.metrics import precision_recall_fscore_support, balanced_accuracy_score

LABELS_42 = [
    "心血瘀阻", "正虚毒瘀", "正虚瘀结", "气滞血瘀", "气虚血瘀", "气血亏虚",
    "气阴两虚", "湿热下注", "湿热瘀阻", "湿热蕴结", "湿热阻络", "热毒蕴结",
    "痰浊瘀阻", "痰浊蒙窍", "痰湿中阻", "痰湿蒙窍", "痰湿蕴肺", "痰瘀互结",
    "痰瘀痹阻", "瘀血阻络", "肝经湿热", "肝肾不足", "肝肾亏虚", "肝肾阴虚",
    "肝胃不和", "肝胃郁热", "肝阳上亢", "肾虚", "脾肾两虚", "脾胃不和",
    "脾胃虚寒", "血热", "血瘀痰凝", "阳虚水泛", "阴虚火旺", "阴虚血瘀",
    "阴虚阳亢", "风寒外袭", "风寒袭肺", "风痰上扰", "风痰入络", "风痰阻络",
]
assert len(LABELS_42) == 42 and len(set(LABELS_42)) == 42

GATE_TOL = 5e-5
FROZEN = {  # v20 tables/full_data_seed42.csv (2026-09-03 SEAL)
    "macbert":   (0.6278, 0.5681, 0.6394, 0.7263),
    "zybert":    (0.7577, 0.6651, 0.7800, 0.7932),
    "qwen3":     (0.5870, 0.5450, 0.6182, 0.6873),
    "internlm3": (0.6958, 0.6074, 0.7220, 0.7355),
}
METRIC_KEYS = ["syn_acc@1", "macro_f1", "weighted_f1", "balanced_accuracy"]


def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def compute_metrics(golds, preds):
    """sklearn 权威口径 (与 v19_pairwise_stats.py::compute_metrics 逐字一致)."""
    n = len(golds)
    acc = sum(1 for g, p in zip(golds, preds) if g == p) / n
    _, _, macro_f1, _ = precision_recall_fscore_support(
        golds, preds, average="macro", labels=LABELS_42, zero_division=0)
    _, _, weighted_f1, _ = precision_recall_fscore_support(
        golds, preds, average="weighted", labels=LABELS_42, zero_division=0)
    bal_acc = balanced_accuracy_score(golds, preds)
    return (round(acc, 4), round(float(macro_f1), 4), round(float(weighted_f1), 4),
            round(float(bal_acc), 4))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--v20-package", type=Path, default=None,
                    help="Optional unpacked v20 evidence package for id/gold/label-order cross-checks.")
    ap.add_argument("--frozen-csv", type=Path, default=None,
                    help="v20 tables/full_data_seed42.csv (默认内嵌冻结值, 可用此交叉校验)")
    args = ap.parse_args()
    root: Path = args.root

    aligned = root / "predictions/four_model_clean4218_seed42.jsonl"
    assert aligned.exists(), f"missing: {aligned}"
    recs = load_jsonl(aligned)
    assert len(recs) == 4218, f"rows={len(recs)} != 4218"
    ids = [r["id"] for r in recs]
    assert len(set(ids)) == 4218, "duplicate ids"
    golds = [r["gold"] for r in recs]
    assert set(golds) <= set(LABELS_42), "gold 超出冻结 label space"

    # 与 v20 冻结 clean 划分交叉校验
    v20 = args.v20_package
    if v20 is not None and v20.exists():
        clean = json.load(open(v20 / "data/heldout_clean_4218.json", encoding="utf-8"))
        assert [it["id"] for it in clean] == ids, "id 顺序 != heldout_clean_4218.json"
        assert [it["syndrome_canonical"] for it in clean] == golds, "gold != clean gold"
        frozen_labels = [l.strip() for l in
                         open(v20 / "data_documentation/labels_42.txt", encoding="utf-8") if l.strip()]
        assert frozen_labels == LABELS_42, "labels_42.txt != 内嵌冻结 list"
        print(f"[交叉校验] v20 {v20}: labels/gold/id 顺序全部一致")

    # 可选: 从 v20 冻结 CSV 读参考值 (否则用内嵌)
    frozen = dict(FROZEN)
    if args.frozen_csv and args.frozen_csv.exists():
        with open(args.frozen_csv, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["model"] in frozen:
                    frozen[r["model"]] = tuple(float(r[k]) for k in METRIC_KEYS)
        print(f"[交叉校验] 冻结参考值来自 {args.frozen_csv}")

    print(f"\n{'model':<10} {'acc':>8} {'macroF1':>9} {'wF1':>8} {'balacc':>8}   冻结表对照 (容差 {GATE_TOL:.0e})")
    ok = True
    for m in ["macbert", "zybert", "qwen3", "internlm3"]:
        got = compute_metrics(golds, [r[m] for r in recs])
        ref = frozen[m]
        diffs = [abs(a - b) for a, b in zip(got, ref)]
        passed = max(diffs) <= GATE_TOL
        ok &= passed
        print(f"{m:<10} {got[0]:>8.4f} {got[1]:>9.4f} {got[2]:>8.4f} {got[3]:>8.4f}   "
              f"max|d|={max(diffs):.2e}  {'PASS' if passed else 'FAIL'}")
        if not passed:
            for k, a, b, d in zip(METRIC_KEYS, got, ref, diffs):
                if d > GATE_TOL:
                    print(f"    {m}.{k}: got {a} vs frozen {b} (|d|={d:.2e})")

    print(f"\n结论: {'PASS — 逐例文件与冻结主表同源 (反向验证 gate 通过)' if ok else 'FAIL — 存在超差, 不得用于正式统计'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
