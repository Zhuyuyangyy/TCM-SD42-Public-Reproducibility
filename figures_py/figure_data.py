#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Single source of truth for every number drawn in Figures 1-8.

Values are loaded from the archived aggregate inputs and the published
authorized-data re-verification audit. Figure scripts call these loaders.
"""
import csv
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "source_data")
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
BA_AUDIT = os.path.join(ROOT, "audits", "20261110_ba_reverification", "results")

SHORT = {"ZY-BERT": "ZY-BERT", "InternLM3": "InternLM3-8B",
         "MacBERT": "MacBERT", "Qwen3": "Qwen3-8B"}
ORDER = ["ZY-BERT", "InternLM3-8B", "MacBERT", "Qwen3-8B"]

SUP = str.maketrans("0123456789-", "\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079\u207b")


def _rows(name, directory=DATA):
    with open(os.path.join(directory, name), encoding="utf-8-sig") as fh:
        yield from csv.DictReader(fh)


def metrics():
    """display name -> dict(acc, mf1, wf1, ba, ci_lo, ci_hi)"""
    out = {}
    for r in _rows("fig5_metrics.csv"):
        out[SHORT[r["model"]]] = dict(
            acc=float(r["accuracy"]), mf1=float(r["macro_f1"]),
            wf1=float(r["weighted_f1"]), ba=float(r["balanced_accuracy"]),
            ci_lo=float(r["acc_ci_lo"]), ci_hi=float(r["acc_ci_hi"]))
    return out


def metric_matrix():
    """4 models x [accuracy, macro-F1, weighted-F1, balanced accuracy]"""
    m = metrics()
    return [[m[n][k] for k in ("acc", "mf1", "wf1", "ba")] for n in ORDER]


def _p_text(s):
    mant, exp = s.split("e")
    return f"{mant} \u00d7 10{str(int(exp)).translate(SUP)}"


def acc_pairs():
    """6 rows: (label, delta, lo, hi, 'discordant a / b', 'p ...')"""
    out = []
    for r in _rows("fig5_pairs.csv"):
        a, b = [SHORT[x.strip()] for x in r["pair"].split("vs")]
        out.append((f"{a} vs {b}", float(r["acc_diff"]), float(r["acc_lo"]),
                    float(r["acc_hi"]), f'{r["mcn_a"]} / {r["mcn_b"]}',
                    _p_text(r["p_holm"])))
    return out


def mf1_forest():
    return [(float(r["mf1_diff"]), float(r["mf1_lo"]), float(r["mf1_hi"]))
            for r in _rows("fig5_pairs.csv")]


def _model_key(name):
    return name.lower().removesuffix("-8b").replace("-", "")


def _pair_key(row):
    return _model_key(row["a"]), _model_key(row["b"])


def ba_forest():
    """Ordinary BA intervals from the authorized-data re-verification."""
    corrected = {
        (r["model_a"], r["model_b"]): tuple(
            100 * float(r[col]) for col in ("diff_obs_full_precision", "ci_lower", "ci_upper")
        )
        for r in _rows("pairwise_balanced_accuracy_bootstrap_seed42_corrected.csv", BA_AUDIT)
    }
    return [corrected[_pair_key(r)] for r in _rows("fig5_pairs.csv")]


def _paired():
    m = metrics()
    r = next(_rows("fig5_pairs.csv"))
    a, b = "ZY-BERT", "InternLM3-8B"
    return (round(m[a]["acc"] - m[b]["acc"], 2),
            float(r["acc_lo"]), float(r["acc_hi"]),
            round(m[a]["mf1"] - m[b]["mf1"], 2),
            float(r["mf1_lo"]), float(r["mf1_hi"]), m)


def primary_pair():
    """(d_acc, acc_lo, acc_hi, d_mf1, mf1_lo, mf1_hi, metrics)"""
    return _paired()


def seeds():
    """model -> [acc at seed 42, 2026, 7]"""
    out = {}
    for r in _rows("fig6_seeds.csv"):
        out.setdefault(SHORT[r["model"]], []).append(float(r["accuracy"]))
    return out


def seed_mean_sd(model):
    v = seeds()[model]
    mu = sum(v) / len(v)
    sd = math.sqrt(sum((x - mu) ** 2 for x in v) / (len(v) - 1))
    return mu, sd


def dedup_slopes():
    """6 rows in panel order: (label, S0, S1, S2); sign = later model - earlier model."""
    raw = {}
    for r in _rows("dedup_sensitivity_seed42.csv", RESULTS):
        a, b = r["pair"].split("-vs-")
        subset = r["subset"][:2]
        delta = float(r["delta_acc_pp"])
        raw[subset, a, b] = delta
        raw[subset, b, a] = -delta
    spec = [("Qwen3 vs ZY-BERT", "ZY-BERT vs Qwen3", -1),
            ("MacBERT vs ZY-BERT", "ZY-BERT vs MacBERT", -1),
            ("InternLM3 vs ZY-BERT", "ZY-BERT vs InternLM3", -1),
            ("MacBERT vs Qwen3", "MacBERT vs Qwen3", 1),
            ("InternLM3 vs MacBERT", "InternLM3 vs MacBERT", 1),
            ("InternLM3 vs Qwen3", "InternLM3 vs Qwen3", 1)]
    out = []
    for label, key, sign in spec:
        a, b = (_model_key(name) for name in key.split(" vs "))
        out.append((label, *(sign * raw[s, a, b] for s in ("S0", "S1", "S2"))))
    return out


def bootstrap_forest():
    """(macro list, balanced-accuracy list), each 6 rows (diff, ord_lo, ord_hi, str_lo, str_hi)"""
    stratified = {
        (r["metric"], r["model_a"], r["model_b"]):
            (100 * float(r["ci_lower"]), 100 * float(r["ci_upper"]))
        for r in _rows("pairwise_class_sensitive_stratified_bootstrap_seed42.csv", RESULTS)
    }
    keys = [_pair_key(r) for r in _rows("fig5_pairs.csv")]
    return tuple(
        [(*ordinary, *stratified[(metric, *key)]) for key, ordinary in zip(keys, values)]
        for metric, values in (("macro_f1", mf1_forest()), ("balanced_accuracy", ba_forest()))
    )


def error_rows():
    """10 rows: (label, [ZY, InternLM3, MacBERT, Qwen3], pooled)"""
    out = []
    for r in _rows("fig8_errors.csv"):
        vals = [int(r["ZY-BERT"]), int(r["InternLM3"]),
                int(r["MacBERT"]), int(r["Qwen3"])]
        out.append((f'{r["true_id"]} \u2192 {r["pred_id"]}', vals, sum(vals)))
    return out


def _summary():
    """model key -> public aggregate row (results/clean4218_seed42.csv)"""
    return {r["model"]: r for r in _rows("model_summary.csv")}


def validity():
    """display name -> (percent, empty count)"""
    key = {"zybert": "ZY-BERT", "internlm3": "InternLM3-8B",
           "macbert": "MacBERT", "qwen3": "Qwen3-8B"}
    out = {}
    for m, r in _summary().items():
        # historical CSV column name; this is the valid-label extraction rate
        # (parser success), not strict compliance with the two-field format
        rate = float(r["format_validity"])
        out[key[m]] = (round(rate * 100, 2), round((1 - rate) * 4218))
    return out


def params():
    """display name -> recorded total parameters (only where recorded)."""
    key = {"zybert": "ZY-BERT", "internlm3": "InternLM3-8B",
           "macbert": "MacBERT", "qwen3": "Qwen3-8B"}
    out = {}
    for m, r in _summary().items():
        if r["total_params"].strip():
            out[key[m]] = int(r["total_params"])
    return out


def param_ratios():
    """(recorded ratio vs InternLM3, nominal 8B ratio) for ZY-BERT."""
    p = params()
    return p["InternLM3-8B"] / p["ZY-BERT"], 8e9 / p["ZY-BERT"]


def support():
    with open(os.path.join(DATA, "classwise_metrics.csv"), encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    return sorted((int(r["support"]) for r in rows), reverse=True)


def n_test():
    return sum(support())


if __name__ == "__main__":
    print("test n =", n_test())
    print("metrics", metrics())
    print("pairs", acc_pairs())
    print("seeds", seeds(), seed_mean_sd("ZY-BERT"), seed_mean_sd("InternLM3-8B"))
    print("validity", validity())
