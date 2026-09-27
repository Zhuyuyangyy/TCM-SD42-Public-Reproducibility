#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pairwise_class_sensitive_bootstrap.py — 四模型 clean4218 六组 pair 的
Macro-F1 / Balanced Accuracy 差值 paired bootstrap (v23 stats addendum, 2026-09-07)

唯一输入:
  predictions/four_model_clean4218_seed42.jsonl   (id, gold, macbert, qwen3, zybert, internlm3)

冻结口径 (与 v19/v18 权威实现逐字一致):
  - label space : data_documentation/labels_42.txt (42 类, 冻结顺序; 脚本内嵌副本,
                  存在 v20 包时与 data_documentation/labels_42.txt 交叉校验)
  - 指标定义    : macro-F1 = sklearn precision_recall_fscore_support(
                    average='macro', labels=LABELS, zero_division=0)   (42 类分母固定)
                  Balanced Accuracy = sklearn balanced_accuracy_score  (union 平均, nan->0)
  - ordinary    : random.Random(20260516) 每 pair 全新实例, rng.choices(idx, k=n),
                  2000 resamples, percentile [50]/[1949], 差值 = first - second
                  (与 v19 accuracy 口径逐字相同; 本脚本在同一 resample 上同时计算 acc/f1/balacc)
  - stratified  : 每 syndrome class 内按该类原始 support 有放回抽样, 按冻结 LABELS 顺序
                  拼回 4218 条; 同一随机种子 (20260516), 独立 RNG 流

硬 gate (任一失败即退出, 不产出任何统计表):
  G1 反向验证 : 四模型 Accuracy/Macro-F1/Weighted-F1/BalAcc 重算值 vs
                冻结 tables/full_data_seed42.csv, 容差 5e-5 (脚本内嵌冻结表 + 可选项交叉校验)
  G2 口径一致性: Accuracy 差值 bootstrap CI 必须精确复现 v19_pairwise_stats.json
                (4dp 逐位一致; 证明 pred 向量与 RNG 流与 v19 逐字相同)
  G3 快速路径 : numpy bincount 快速指标 vs sklearn 在 50 个随机样本上 allclose 1e-12

用法:
  python3 evaluation/pairwise_class_sensitive_bootstrap.py [--root DIR]
输出:
  tables/pairwise_macro_f1_bootstrap_seed42.csv
  tables/pairwise_balanced_accuracy_bootstrap_seed42.csv
  tables/pairwise_class_sensitive_bootstrap_seed42.csv
  sensitivity/pairwise_class_sensitive_stratified_bootstrap_seed42.csv
"""
import argparse
import csv
import json
import random
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import precision_recall_fscore_support, balanced_accuracy_score

# ── 冻结常量 ─────────────────────────────────────────────────────────
BOOT_SEED = 20260516
N_RESAMPLES = 2000
CI_LO_IDX, CI_HI_IDX = 50, 1949        # percentile [50]/[1949]
N_CLASSES = 42
GATE_TOL = 5e-5                        # G1 容差 (舍入级)

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

# 冻结主表 (v20 tables/full_data_seed42.csv, 2026-09-03 SEAL) — G1 参考
FROZEN_FOUR_MODEL = {
    "macbert":   {"syn_acc@1": 0.6278, "macro_f1": 0.5681, "weighted_f1": 0.6394, "balanced_accuracy": 0.7263},
    "zybert":    {"syn_acc@1": 0.7577, "macro_f1": 0.6651, "weighted_f1": 0.78,   "balanced_accuracy": 0.7932},
    "qwen3":     {"syn_acc@1": 0.587,  "macro_f1": 0.545,  "weighted_f1": 0.6182, "balanced_accuracy": 0.6873},
    "internlm3": {"syn_acc@1": 0.6958, "macro_f1": 0.6074, "weighted_f1": 0.722,  "balanced_accuracy": 0.7355},
}

# 冻结 v19 accuracy 配对 CI (v20 statistics/v19_pairwise_stats.json) — G2 参考
# key = (a, b), 值为 (diff_obs, ci_lower, ci_upper) 4dp
V19_ACC_CI = {
    ("macbert", "qwen3"):     (0.0408,  0.0249,  0.0571),
    ("macbert", "internlm3"): (-0.0680, -0.0830, -0.0533),
    ("macbert", "zybert"):    (-0.1299, -0.1439, -0.1164),
    ("qwen3", "internlm3"):   (-0.1088, -0.1214, -0.0963),
    ("qwen3", "zybert"):      (-0.1707, -0.1844, -0.1574),
    ("internlm3", "zybert"):  (-0.0619, -0.0744, -0.0493),
}

# 六组 pair (用户指定顺序; 差值 = first - second)
PAIRS = [
    ("zybert", "internlm3"),
    ("zybert", "macbert"),
    ("zybert", "qwen3"),
    ("internlm3", "macbert"),
    ("internlm3", "qwen3"),
    ("macbert", "qwen3"),
]
METRICS = ["macro_f1", "balanced_accuracy"]


def load_aligned(p: Path):
    recs = [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]
    assert len(recs) == 4218, f"aligned file: {len(recs)} rows != 4218"
    ids = [r["id"] for r in recs]
    assert len(set(ids)) == 4218, "aligned file: duplicate ids"
    golds = [r["gold"] for r in recs]
    assert set(golds) <= set(LABELS_42), "aligned file: gold outside frozen label space"
    preds = {m: [r[m] for r in recs] for m in FROZEN_FOUR_MODEL}
    for m, pv in preds.items():
        assert set(pv) <= set(LABELS_42) | {"empty"}, f"{m}: pred outside 42 labels/empty"
    return ids, golds, preds


def metrics_sklearn(golds, preds):
    """v19 权威口径 (逐字复刻 v19_pairwise_stats.py::compute_metrics)."""
    n = len(golds)
    acc = sum(1 for g, p in zip(golds, preds) if g == p) / n
    _, _, macro_f1, _ = precision_recall_fscore_support(
        golds, preds, average="macro", labels=LABELS_42, zero_division=0)
    _, _, weighted_f1, _ = precision_recall_fscore_support(
        golds, preds, average="weighted", labels=LABELS_42, zero_division=0)
    bal_acc = balanced_accuracy_score(golds, preds)
    return {"syn_acc@1": round(acc, 4), "macro_f1": round(float(macro_f1), 4),
            "weighted_f1": round(float(weighted_f1), 4), "balanced_accuracy": round(float(bal_acc), 4)}


def fast_metrics(g: np.ndarray, p: np.ndarray):
    """numpy bincount 快速路径 — 逐位复刻 sklearn 语义 (见 G3 自检).
    g/p: int64 数组, 0..41 为冻结 42 类, 42 代表 out-of-label ("empty").
    """
    n = g.shape[0]
    correct = g == p
    acc = correct.sum() / n
    wrong = ~correct
    tp = np.bincount(g[correct], minlength=N_CLASSES + 1)[:N_CLASSES]
    fp = np.bincount(p[wrong], minlength=N_CLASSES + 1)[:N_CLASSES]
    fn = np.bincount(g[wrong], minlength=N_CLASSES + 1)[:N_CLASSES]
    denom = 2 * tp + fp + fn
    f1 = np.divide(2 * tp, denom, out=np.zeros(N_CLASSES, dtype=np.float64), where=denom > 0)
    macro_f1 = f1.mean()  # 分母固定 42 类 (labels=LABELS)
    # balanced accuracy: sklearn 对 union(gold, pred) 求 recall 均值, 0 行 -> nan -> 0
    row = np.bincount(g, minlength=N_CLASSES + 1)
    pred_row = np.bincount(p, minlength=N_CLASSES + 1)
    union = (row + pred_row) > 0
    rec = np.divide(tp, row[:N_CLASSES], out=np.zeros(N_CLASSES, dtype=np.float64),
                    where=row[:N_CLASSES] > 0)
    balacc = rec[union[:N_CLASSES]].mean()
    return acc, macro_f1, balacc


def ci_of(diffs):
    diffs = np.sort(np.asarray(diffs))
    return round(float(diffs[CI_LO_IDX]), 4), round(float(diffs[CI_HI_IDX]), 4)


def run_ordinary(gold_idx: np.ndarray, pa_idx: np.ndarray, pb_idx: np.ndarray):
    """v19 逐字 RNG: random.Random(20260516) 每 pair 新实例, rng.choices(idx, k=n).
    返回每 resample 的 (acc, macro_f1, balacc) 差值数组."""
    rng = random.Random(BOOT_SEED)
    n = gold_idx.shape[0]
    idx = list(range(n))
    d_acc, d_f1, d_ba = [], [], []
    for _ in range(N_RESAMPLES):
        rs = np.array(rng.choices(idx, k=n), dtype=np.int64)
        g = gold_idx[rs]
        acc_a, f1_a, ba_a = fast_metrics(g, pa_idx[rs])
        acc_b, f1_b, ba_b = fast_metrics(g, pb_idx[rs])
        d_acc.append(acc_a - acc_b)
        d_f1.append(f1_a - f1_b)
        d_ba.append(ba_a - ba_b)
    return np.asarray(d_acc), np.asarray(d_f1), np.asarray(d_ba)


def run_stratified(gold_idx: np.ndarray, pa_idx: np.ndarray, pb_idx: np.ndarray):
    """class-stratified: 每类按原始 support 有放回抽样, 冻结 LABELS 顺序拼回 n 条."""
    rng = random.Random(BOOT_SEED)
    pos = {c: np.where(gold_idx == c)[0] for c in range(N_CLASSES)}
    d_acc, d_f1, d_ba = [], [], []
    for _ in range(N_RESAMPLES):
        parts = []
        for c in range(N_CLASSES):
            pool = pos[c]
            parts.append(pool[rng.choices(range(len(pool)), k=len(pool))])
        rs = np.concatenate(parts) if parts else np.empty(0, dtype=np.int64)
        g = gold_idx[rs]
        acc_a, f1_a, ba_a = fast_metrics(g, pa_idx[rs])
        acc_b, f1_b, ba_b = fast_metrics(g, pb_idx[rs])
        d_acc.append(acc_a - acc_b)
        d_f1.append(f1_a - f1_b)
        d_ba.append(ba_a - ba_b)
    return np.asarray(d_acc), np.asarray(d_f1), np.asarray(d_ba)


def gate_g1(golds, preds):
    """G1 反向验证: 四模型 4 指标 vs 冻结主表 (<=5e-5)."""
    print("[G1] 反向验证: 四模型指标 vs 冻结 full_data_seed42.csv")
    ok = True
    for m in FROZEN_FOUR_MODEL:
        got = metrics_sklearn(golds, preds[m])
        ref = FROZEN_FOUR_MODEL[m]
        for k in ["syn_acc@1", "macro_f1", "weighted_f1", "balanced_accuracy"]:
            d = abs(got[k] - ref[k])
            if d > GATE_TOL:
                ok = False
                print(f"  FAIL {m}.{k}: got {got[k]} vs frozen {ref[k]} (|d|={d:.2e} > 5e-5)")
        print(f"  {m:<10} acc={got['syn_acc@1']:.4f} mF1={got['macro_f1']:.4f} "
              f"wF1={got['weighted_f1']:.4f} balacc={got['balanced_accuracy']:.4f} "
              f"{'PASS' if all(abs(got[k]-ref[k]) <= GATE_TOL for k in ref) else 'FAIL'}")
    return ok


def gate_g2(gold_idx, pred_idx):
    """G2 口径一致性: Accuracy 差值 CI 精确复现 v19 (4dp)."""
    print("[G2] Accuracy 差值 CI vs v19_pairwise_stats.json (4dp 精确)")
    ok = True
    for (a, b), (ref_diff, ref_lo, ref_hi) in V19_ACC_CI.items():
        d_acc, _, _ = run_ordinary(gold_idx, pred_idx[a], pred_idx[b])
        lo, hi = ci_of(d_acc)
        obs_diff = round(float(np.mean(d_acc)), 4)  # 均值 = (acc_a - acc_b) 的 bootstrap 均值
        match = (lo == ref_lo and hi == ref_hi)
        ok &= match
        print(f"  {a}_vs_{b}: CI=[{lo:.4f},{hi:.4f}] ref=[{ref_lo:.4f},{ref_hi:.4f}] "
              f"{'PASS' if match else 'FAIL'}")
    return ok


def raw_sklearn(golds_list, preds_list):
    """未舍入 sklearn 权威值 (G3 参考): 与 fast_metrics 全精度比对, 避免 4dp 舍入误差."""
    n = len(golds_list)
    acc = sum(1 for g, p in zip(golds_list, preds_list) if g == p) / n
    _, _, macro_f1, _ = precision_recall_fscore_support(
        golds_list, preds_list, average="macro", labels=LABELS_42, zero_division=0)
    _, _, weighted_f1, _ = precision_recall_fscore_support(
        golds_list, preds_list, average="weighted", labels=LABELS_42, zero_division=0)
    bal_acc = balanced_accuracy_score(golds_list, preds_list)
    return acc, float(macro_f1), float(bal_acc)


def gate_g3(gold_idx, pred_idx, golds, preds):
    """G3 快速路径 vs sklearn 在 50 个随机样本上逐位一致 (未舍入参考, allclose 1e-12)."""
    print("[G3] numpy 快速路径 vs sklearn (50 随机样本, allclose 1e-12)")
    rng = random.Random(12345)
    n = gold_idx.shape[0]
    idx = list(range(n))
    lab2i = {l: i for i, l in enumerate(LABELS_42)}
    ok = True
    for _ in range(50):
        rs = rng.choices(idx, k=n)
        g = np.array([gold_idx[i] for i in rs], dtype=np.int64)
        for m in FROZEN_FOUR_MODEL:
            p = np.array([pred_idx[m][i] for i in rs], dtype=np.int64)
            acc, mf, ba = fast_metrics(g, p)
            gs = [golds[i] for i in rs]
            ps = [preds[m][i] for i in rs]
            ref = raw_sklearn(gs, ps)
            if not (np.isclose(acc, ref[0], atol=1e-12)
                    and np.isclose(mf, ref[1], atol=1e-12)
                    and np.isclose(ba, ref[2], atol=1e-12)):
                ok = False
                print(f"  FAIL {m}: fast=({acc:.12f},{mf:.12f},{ba:.12f}) "
                      f"sklearn=({ref[0]:.12f},{ref[1]:.12f},{ref[2]:.12f})")
    print(f"  {'PASS (50/50)' if ok else 'FAIL'}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--v20-package", type=Path, default=None,
                    help="v20 冻结包路径 (存在时交叉校验冻结表/labels/v19 CI; 默认自动探测)")
    args = ap.parse_args()
    root: Path = args.root

    aligned = root / "predictions/four_model_clean4218_seed42.jsonl"
    assert aligned.exists(), f"missing input: {aligned}"
    ids, golds, preds = load_aligned(aligned)
    print(f"input: {aligned}  n={len(ids)}")

    # 可选: 与本地 v20 冻结文件交叉校验；默认不假设私有服务器路径。
    v20 = args.v20_package
    if v20 is not None and v20.exists():
        frozen_labels = [l.strip() for l in (v20 / "data_documentation/labels_42.txt").open(encoding="utf-8")
                         if l.strip()]
        assert frozen_labels == LABELS_42, "labels_42.txt 与内嵌冻结 list 不一致"
        clean = json.load(open(v20 / "data/heldout_clean_4218.json", encoding="utf-8"))
        clean_ids = [it["id"] for it in clean]
        assert clean_ids == ids, "aligned id 顺序 != heldout_clean_4218.json 顺序"
        assert [it["syndrome_canonical"] for it in clean] == golds, "aligned gold != clean gold"
        print(f"[交叉校验] v20 {v20}: labels/gold/ids 全部一致")

    lab2i = {l: i for i, l in enumerate(LABELS_42)}
    gold_idx = np.array([lab2i[g] for g in golds], dtype=np.int64)
    pred_idx = {m: np.array([lab2i.get(p, N_CLASSES) for p in pv], dtype=np.int64)
                for m, pv in preds.items()}  # 42 = out-of-label ("empty")

    # ── 硬 gate (全过才产出统计) ──
    ok = gate_g1(golds, preds)
    ok &= gate_g3(gold_idx, pred_idx, golds, preds)
    ok &= gate_g2(gold_idx, pred_idx)
    if not ok:
        print("\nGATE FAILED — 不产出任何正式统计表。")
        sys.exit(1)
    print("\n全部 gate 通过, 开始正式 bootstrap 计算...\n")

    # ── 正式计算 ──
    obs = {}      # (pair, metric) -> observed diff (4dp)
    ord_ci = {}   # (pair, metric) -> (lo, hi)
    str_ci = {}
    for a, b in PAIRS:
        oa = metrics_sklearn(golds, preds[a])
        ob = metrics_sklearn(golds, preds[b])
        for met in METRICS:
            obs[(a, b, met)] = round(oa[met] - ob[met], 4)
        d_acc, d_f1, d_ba = run_ordinary(gold_idx, pred_idx[a], pred_idx[b])
        ord_ci[(a, b, "macro_f1")] = ci_of(d_f1)
        ord_ci[(a, b, "balanced_accuracy")] = ci_of(d_ba)
        s_acc, s_f1, s_ba = run_stratified(gold_idx, pred_idx[a], pred_idx[b])
        str_ci[(a, b, "macro_f1")] = ci_of(s_f1)
        str_ci[(a, b, "balanced_accuracy")] = ci_of(s_ba)
        print(f"  {a} vs {b}: mF1 diff={obs[(a,b,'macro_f1')]:+.4f} "
              f"ord CI=[{ord_ci[(a,b,'macro_f1')][0]:+.4f},{ord_ci[(a,b,'macro_f1')][1]:+.4f}] "
              f"strat CI=[{str_ci[(a,b,'macro_f1')][0]:+.4f},{str_ci[(a,b,'macro_f1')][1]:+.4f}] | "
              f"balacc diff={obs[(a,b,'balanced_accuracy')]:+.4f} "
              f"ord CI=[{ord_ci[(a,b,'balanced_accuracy')][0]:+.4f},{ord_ci[(a,b,'balanced_accuracy')][1]:+.4f}] "
              f"strat CI=[{str_ci[(a,b,'balanced_accuracy')][0]:+.4f},{str_ci[(a,b,'balanced_accuracy')][1]:+.4f}]")

    # ── 写表 ──
    def excl_zero(ci):
        return ci[0] > 0 or ci[1] < 0

    def agree(ord_ci_, str_ci_):
        o_ex = excl_zero(ord_ci_); s_ex = excl_zero(str_ci_)
        if o_ex != s_ex:
            return False
        if not o_ex:
            return True  # 都含 0
        return (ord_ci_[0] > 0) == (str_ci_[0] > 0)  # 都排除 0 且同侧

    tables = root / "tables"; sens = root / "sensitivity"
    tables.mkdir(parents=True, exist_ok=True); sens.mkdir(parents=True, exist_ok=True)

    with open(tables / "pairwise_macro_f1_bootstrap_seed42.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pair", "model_a", "model_b", "n", "macro_f1_a", "macro_f1_b",
                    "diff_obs", "ci_lower", "ci_upper", "ci_excludes_zero",
                    "method", "n_resamples", "seed"])
        for a, b in PAIRS:
            va = metrics_sklearn(golds, preds[a])["macro_f1"]; vb = metrics_sklearn(golds, preds[b])["macro_f1"]
            lo, hi = ord_ci[(a, b, "macro_f1")]
            w.writerow([f"{a}_vs_{b}", a, b, len(golds), va, vb, obs[(a, b, "macro_f1")],
                        lo, hi, excl_zero((lo, hi)), "ordinary_paired", N_RESAMPLES, BOOT_SEED])

    with open(tables / "pairwise_balanced_accuracy_bootstrap_seed42.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pair", "model_a", "model_b", "n", "balanced_accuracy_a", "balanced_accuracy_b",
                    "diff_obs", "ci_lower", "ci_upper", "ci_excludes_zero",
                    "method", "n_resamples", "seed"])
        for a, b in PAIRS:
            va = metrics_sklearn(golds, preds[a])["balanced_accuracy"]
            vb = metrics_sklearn(golds, preds[b])["balanced_accuracy"]
            lo, hi = ord_ci[(a, b, "balanced_accuracy")]
            w.writerow([f"{a}_vs_{b}", a, b, len(golds), va, vb, obs[(a, b, "balanced_accuracy")],
                        lo, hi, excl_zero((lo, hi)), "ordinary_paired", N_RESAMPLES, BOOT_SEED])

    with open(tables / "pairwise_class_sensitive_bootstrap_seed42.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pair", "model_a", "model_b", "metric", "value_a", "value_b",
                    "diff_obs", "ci_lower", "ci_upper", "ci_excludes_zero",
                    "n", "n_resamples", "seed", "method"])
        for a, b in PAIRS:
            for met in METRICS:
                va = metrics_sklearn(golds, preds[a])[met]; vb = metrics_sklearn(golds, preds[b])[met]
                lo, hi = ord_ci[(a, b, met)]
                w.writerow([f"{a}_vs_{b}", a, b, met, va, vb, obs[(a, b, met)],
                            lo, hi, excl_zero((lo, hi)), len(golds), N_RESAMPLES, BOOT_SEED,
                            "ordinary_paired"])

    with open(sens / "pairwise_class_sensitive_stratified_bootstrap_seed42.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pair", "model_a", "model_b", "metric", "value_a", "value_b",
                    "diff_obs", "ci_lower", "ci_upper", "ci_excludes_zero",
                    "ordinary_ci_lower", "ordinary_ci_upper", "direction_agrees",
                    "n", "n_resamples", "seed", "method"])
        for a, b in PAIRS:
            for met in METRICS:
                va = metrics_sklearn(golds, preds[a])[met]; vb = metrics_sklearn(golds, preds[b])[met]
                lo, hi = str_ci[(a, b, met)]
                o_lo, o_hi = ord_ci[(a, b, met)]
                w.writerow([f"{a}_vs_{b}", a, b, met, va, vb, obs[(a, b, met)],
                            lo, hi, excl_zero((lo, hi)), o_lo, o_hi, agree((o_lo, o_hi), (lo, hi)),
                            len(golds), N_RESAMPLES, BOOT_SEED, "class_stratified"])

    print("\n[tables] pairwise_macro_f1_bootstrap_seed42.csv")
    print("[tables] pairwise_balanced_accuracy_bootstrap_seed42.csv")
    print("[tables] pairwise_class_sensitive_bootstrap_seed42.csv")
    print("[sensitivity] pairwise_class_sensitive_stratified_bootstrap_seed42.csv")
    print("\nDONE")


if __name__ == "__main__":
    main()
