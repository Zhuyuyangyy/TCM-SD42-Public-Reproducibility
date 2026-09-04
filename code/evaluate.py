#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified evaluation script — six metrics + bootstrap CI + McNemar.
All experiments use this script. Do NOT write per-experiment evaluators.

Metrics (six):
1. syn_acc@1: exact match accuracy
2. macro_f1: macro-averaged F1 (scikit-learn)
3. weighted_f1: weighted-averaged F1
4. balanced_accuracy: balanced accuracy
5. format_validity: % of parseable outputs
6. empty_pred_rate: % of empty predictions

Plus:
- syn@1 bootstrap CI (2000 resamples, seed=20260516)
- McNemar exact test (binomial, two-sided)
- Confusion matrix export
"""

import json
import random
import csv
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    balanced_accuracy_score,
    confusion_matrix,
)

# ── Constants ───────────────────────────────────────────────────────
BOOTSTRAP_N = 2000
BOOTSTRAP_SEED = 20260516
CI_ALPHA = 0.05  # 95% CI

# ── Label loading ──────────────────────────────────────────────────
_LABELS_FILE = Path(__file__).parent / "labels_42.txt"
if not _LABELS_FILE.exists():
    _LABELS_FILE = Path(__file__).parent.parent / "shared" / "labels_42.txt"

with open(_LABELS_FILE, "r", encoding="utf-8") as f:
    LABELS_42 = [line.strip() for line in f if line.strip()]


def compute_metrics(
    gold_labels: List[str],
    pred_labels: List[str],
    label_list: Optional[List[str]] = None,
) -> Dict:
    """
    Compute six metrics from gold and predicted labels.
    
    Args:
        gold_labels: ground truth labels
        pred_labels: predicted labels
        label_list: full label set (default: 42 labels from labels_42.txt)
    
    Returns:
        dict with all metrics
    """
    if label_list is None:
        label_list = LABELS_42

    n = len(gold_labels)
    assert len(pred_labels) == n, f"Length mismatch: {len(gold_labels)} vs {len(pred_labels)}"

    # syn_acc@1 (exact match accuracy)
    syn_acc1 = sum(1 for g, p in zip(gold_labels, pred_labels) if g == p) / n

    # Format validity (percentage of non-empty, parseable predictions)
    format_valid = sum(1 for p in pred_labels if p != "empty") / n

    # Empty prediction rate
    empty_rate = sum(1 for p in pred_labels if p == "empty") / n

    # Compute precision, recall, f1 with sklearn
    # Handle case where all predictions are "empty" — sklearn may warn
    try:
        macro_prec, macro_rec, macro_f1, _ = precision_recall_fscore_support(
            gold_labels, pred_labels, average="macro", labels=label_list, zero_division=0
        )
        weighted_prec, weighted_rec, weighted_f1, _ = precision_recall_fscore_support(
            gold_labels, pred_labels, average="weighted", labels=label_list, zero_division=0
        )
    except Exception:
        macro_f1 = 0.0
        weighted_f1 = 0.0

    # Balanced accuracy
    try:
        bal_acc = balanced_accuracy_score(gold_labels, pred_labels)
    except Exception:
        bal_acc = 0.0

    # Per-class metrics
    class_metrics = {}
    try:
        cm = confusion_matrix(gold_labels, pred_labels, labels=label_list)
        for i, label in enumerate(label_list):
            tp = cm[i, i]
            fp = cm[:, i].sum() - tp
            fn = cm[i, :].sum() - tp
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
            support = cm[i, :].sum()
            class_metrics[label] = {
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1": round(f1, 4),
                "support": int(support),
            }
    except Exception as e:
        class_metrics = {"error": str(e)}

    return {
        "n": n,
        "syn_acc@1": round(syn_acc1, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "balanced_accuracy": round(bal_acc, 4),
        "format_validity": round(format_valid, 4),
        "empty_pred_rate": round(empty_rate, 4),
        "per_class": class_metrics,
    }


def bootstrap_ci(
    gold_labels: List[str],
    pred_labels: List[str],
    n_resamples: int = BOOTSTRAP_N,
    seed: int = BOOTSTRAP_SEED,
    alpha: float = CI_ALPHA,
) -> Dict:
    """
    Bootstrap confidence interval for syn_acc@1.
    NOTE (2026-08-05): 实现为整体有放回重采样 (non-stratified paired bootstrap),
    seed=20260516, 2000 resamples. 早期 docstring 写 "Stratified by label" 是错误描述,
    实际从未分层; 现与 parser_specification.md 口径一致 (冻结行为以实现为准)。

    Returns:
        dict with ci_lower, ci_upper, ci_median, std_err
    """
    rng = random.Random(seed)
    n = len(gold_labels)
    indices = list(range(n))

    accuracies = []
    for _ in range(n_resamples):
        # Resample with replacement
        resampled = rng.choices(indices, k=n)
        correct = sum(1 for i in resampled if gold_labels[i] == pred_labels[i])
        accuracies.append(correct / n)

    accuracies.sort()
    lower_idx = int(n_resamples * alpha / 2)
    upper_idx = int(n_resamples * (1 - alpha / 2))

    return {
        "n_resamples": n_resamples,
        "seed": seed,
        "ci_lower": round(accuracies[lower_idx], 4),
        "ci_upper": round(accuracies[upper_idx], 4),
        "ci_median": round(accuracies[n_resamples // 2], 4),
        "std_err": round(np.std(accuracies, ddof=1).item(), 4),
    }


def mcnemar_exact(
    gold_labels: List[str],
    pred_labels_a: List[str],
    pred_labels_b: List[str],
) -> Dict:
    """
    McNemar exact test (binomial, two-sided).
    Compares two models' predictions against the same gold labels.
    
    n01 = # where model A is wrong, model B is correct
    n10 = # where model A is correct, model B is wrong
    
    Under H0: P(n01 != n10) = binomial test, p = 0.5
    
    Returns:
        dict with n01, n10, p_value, statistic (chi-square approx)
    """
    assert len(gold_labels) == len(pred_labels_a) == len(pred_labels_b)

    n01 = 0  # A wrong, B correct
    n10 = 0  # A correct, B wrong
    n00 = 0  # both wrong
    n11 = 0  # both correct

    for g, a, b in zip(gold_labels, pred_labels_a, pred_labels_b):
        a_correct = g == a
        b_correct = g == b
        if a_correct and b_correct:
            n11 += 1
        elif a_correct and not b_correct:
            n10 += 1
        elif not a_correct and b_correct:
            n01 += 1
        else:
            n00 += 1

    # McNemar exact test (binomial)
    from scipy.stats import binomtest
    p_value = binomtest(n01, n01 + n10, p=0.5).pvalue

    # Also compute chi-square approximation for reference
    from scipy.stats import chi2
    chi2_stat = (n01 - n10) ** 2 / (n01 + n10) if (n01 + n10) > 0 else 0.0
    chi2_p = 1 - chi2.cdf(chi2_stat, 1) if (n01 + n10) > 0 else 1.0

    return {
        "n": len(gold_labels),
        "n00": n00,  # both wrong
        "n01": n01,  # A wrong, B correct
        "n10": n10,  # A correct, B wrong
        "n11": n11,  # both correct
        "discordant_pairs": n01 + n10,
        # 2026-08-05: 保存完整浮点精度, 显示层再格式化 (之前 round(p,6) 会吞掉 4.6e-7 这类小值)
        "p_value_exact": float(p_value),
        "chi2_stat": round(chi2_stat, 4),
        "chi2_p_value": float(chi2_p),
        "method": "McNemar exact test (binomial, two-sided)",
    }


def confusion_matrix_df(
    gold_labels: List[str],
    pred_labels: List[str],
    label_list: Optional[List[str]] = None,
) -> np.ndarray:
    """Return confusion matrix as numpy array."""
    if label_list is None:
        label_list = LABELS_42
    return confusion_matrix(gold_labels, pred_labels, labels=label_list)


def save_metrics_csv(metrics: Dict, output_path: Path):
    """Save metrics to CSV."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for key, value in metrics.items():
            if key != "per_class":
                writer.writerow([key, value])
        # Also save per-class metrics
        if "per_class" in metrics and isinstance(metrics["per_class"], dict):
            writer.writerow([])
            writer.writerow(["per_class_metrics"])
            writer.writerow(["label", "precision", "recall", "f1", "support"])
            for label, cm in metrics["per_class"].items():
                if isinstance(cm, dict):
                    writer.writerow([
                        label,
                        cm.get("precision", ""),
                        cm.get("recall", ""),
                        cm.get("f1", ""),
                        cm.get("support", ""),
                    ])


def load_predictions(predictions_path: Path) -> Tuple[List[str], List[str]]:
    """
    Load gold and pred labels from predictions.jsonl.
    Format per line: {"gold": "...", "pred": "..."}
    """
    golds, preds = [], []
    with open(predictions_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            golds.append(item["gold"])
            preds.append(item["pred"])
    return golds, preds


if __name__ == "__main__":
    # Quick smoke test
    gold = ["心血瘀阻", "痰浊瘀阻", "心血瘀阻", "气滞血瘀"]
    pred = ["心血瘀阻", "痰浊瘀阻", "气滞血瘀", "气滞血瘀"]

    metrics = compute_metrics(gold, pred)
    print("=== Metrics ===")
    for k, v in metrics.items():
        if k != "per_class":
            print(f"  {k}: {v}")

    ci = bootstrap_ci(gold, pred)
    print("\n=== Bootstrap CI ===")
    for k, v in ci.items():
        print(f"  {k}: {v}")

    # McNemar test
    pred_b = ["心血瘀阻", "痰浊瘀阻", "心血瘀阻", "气滞血瘀"]
    mn = mcnemar_exact(gold, pred, pred_b)
    print("\n=== McNemar ===")
    for k, v in mn.items():
        print(f"  {k}: {v}")

    print("\nAll tests passed!")
