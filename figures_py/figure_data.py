#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Single source of truth for every number drawn in Figures 1-8.

All values are read from source_data/ (copied verbatim from the audited
recompute package).  Figure scripts must not hard-code a metric: if a value
is missing here, add a loader, do not type the number into the drawing code.
"""
import csv
import math
import os

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source_data")

SHORT = {"ZY-BERT": "ZY-BERT", "InternLM3": "InternLM3-8B",
         "MacBERT": "MacBERT", "Qwen3": "Qwen3-8B"}
ORDER = ["ZY-BERT", "InternLM3-8B", "MacBERT", "Qwen3-8B"]

SUP = str.maketrans("0123456789-", "\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079\u207b")


def _rows(name):
    with open(os.path.join(DATA, name), encoding="utf-8-sig") as fh:
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


def ba_forest():
    return [(float(r["ba_diff"]), float(r["ba_lo"]), float(r["ba_hi"]))
            for r in _rows("fig5_pairs.csv")]


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
    raw = {r["pair"]: (float(r["S0"]), float(r["S1"]), float(r["S2"]))
           for r in _rows("fig6_dedup.csv")}
    spec = [("Qwen3 vs ZY-BERT", "ZY-BERT vs Qwen3", -1),
            ("MacBERT vs ZY-BERT", "ZY-BERT vs MacBERT", -1),
            ("InternLM3 vs ZY-BERT", "ZY-BERT vs InternLM3", -1),
            ("MacBERT vs Qwen3", "MacBERT vs Qwen3", 1),
            ("InternLM3 vs MacBERT", "InternLM3 vs MacBERT", 1),
            ("InternLM3 vs Qwen3", "InternLM3 vs Qwen3", 1)]
    out = []
    for label, key, sign in spec:
        s0, s1, s2 = raw[key]
        out.append((label, sign * s0, sign * s1, sign * s2))
    return out


def bootstrap_forest():
    """(macro list, balanced-accuracy list), each 6 rows (diff, ord_lo, ord_hi, str_lo, str_hi)"""
    macro, ba = [], []
    for r in _rows("fig6_bootstrap.csv"):
        t = (float(r["diff"]), float(r["ord_lo"]), float(r["ord_hi"]),
             float(r["str_lo"]), float(r["str_hi"]))
        (macro if r["metric"] == "Macro-F1" else ba).append(t)
    return macro, ba


def bootstrap_sources():
    return {r["metric"]: r["str_source"] for r in _rows("fig6_bootstrap.csv")}


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
