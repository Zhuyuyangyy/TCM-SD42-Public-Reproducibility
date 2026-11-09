#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recompute every metric from the raw confusion matrices and check the
archived tables, then check that the rendered SVGs carry those numbers.

Run:  python verify_provenance.py    (exit code 0 = all checks passed)
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "source_data")
FIG = ["Figure%d.svg" % i for i in range(1, 9)]


def matrix(model):
    path = os.path.join(DATA, f"confusion_matrix_{model}.csv")
    with open(path, encoding="utf-8-sig") as fh:
        raw = [r for r in csv.reader(fh) if r and any(c.strip() for c in r)]
    names = [c.strip() for c in raw[0][1:]]
    rows = {}
    for r in raw[1:]:
        rows[r[0].strip()] = [int(float(x)) for x in r[1:]]
    return names, rows


def scores(model):
    """Recompute metrics exactly as archived: empty LLM outputs count as misses."""
    names, rows = matrix(model)
    with open(os.path.join(DATA, "classwise_metrics.csv"), encoding="utf-8-sig") as fh:
        cw = {r["label"]: int(r["support"]) for r in csv.DictReader(fh)}
    support = {n: cw[n] for n in names}
    total = sum(support.values())
    correct = sum(rows[n][i] for i, n in enumerate(names))
    col = {n: sum(rows[r][i] for r in names) for i, n in enumerate(names)}
    rec = {n: rows[n][i] / support[n] for i, n in enumerate(names) if support[n]}
    prec = {n: rows[n][i] / col[n] for i, n in enumerate(names) if col[n]}
    f1 = {n: 2 * prec[n] * rec[n] / (prec[n] + rec[n]) for n in rec if prec.get(n)}
    return dict(total=total, matrix_total=sum(sum(v) for v in rows.values()),
                accuracy=correct / total,
                macro_f1=sum(f1.values()) / len(names),
                weighted_f1=sum(f1[n] * support[n] for n in f1) / total,
                balanced_accuracy=sum(rec.values()) / len(names),
                support=support)


def table(name):
    with open(os.path.join(DATA, name), encoding="utf-8-sig") as fh:
        return {r["model"] if "model" in r else r.get("label", ""): r
                for r in csv.DictReader(fh)}


def check_svg(fig, needles):
    s = open(os.path.join(HERE, fig), encoding="utf-8").read()
    txt = re.sub(r"<[^>]+>", " ", s)
    txt = txt.replace("&amp;", "&").replace("&#x2212;", "\u2212")
    return [n for n in needles if n not in txt]


def main():
    fails = []
    raw = {"zybert": "ZY-BERT", "internlm3": "InternLM3",
           "macbert": "MacBERT", "qwen3": "Qwen3"}
    tab = {r["model"]: r for r in csv.DictReader(
        open(os.path.join(DATA, "fig5_metrics.csv"), encoding="utf-8-sig"))}
    print("== recompute from confusion matrices ==")
    for m, disp in raw.items():
        s = scores(m)
        t = tab[disp]
        line = (f"{disp:10s} n={s['matrix_total']:5d} (+{s['total']-s['matrix_total']} empty) "
                f"acc={s['accuracy']*100:.2f} macroF1={s['macro_f1']*100:.2f} "
                f"wF1={s['weighted_f1']*100:.2f} balAcc={s['balanced_accuracy']*100:.2f}")
        print(line)
        for key, col in (("accuracy", "accuracy"), ("macro_f1", "macro_f1"),
                         ("weighted_f1", "weighted_f1"),
                         ("balanced_accuracy", "balanced_accuracy")):
            if abs(s[key] * 100 - float(t[col])) > 0.005:
                fails.append(f"{disp} {key}: recomputed {s[key]*100:.4f} vs table {t[col]}")
        if s["matrix_total"] + (s["total"] - s["matrix_total"]) != 4218:
            fails.append(f"{disp} denominator {s['total']} != 4218")

    print("\n== support ==")
    sup = scores("zybert")["support"]
    cw = {r["label"]: int(r["support"]) for r in csv.DictReader(
        open(os.path.join(DATA, "classwise_metrics.csv"), encoding="utf-8-sig"))}
    diff = [k for k in cw if sup.get(k) != cw[k]]
    print(f"42-class support sum = {sum(sup.values())}, range {min(sup.values())}-{max(sup.values())}, "
          f"mismatches vs classwise_metrics = {len(diff)}")
    if diff:
        fails.append(f"support mismatch: {diff[:5]}")

    print("\n== seed means ==")
    with open(os.path.join(DATA, "fig6_seeds.csv"), encoding="utf-8-sig") as fh:
        seeds = {}
        for r in csv.DictReader(fh):
            seeds.setdefault(r["model"], []).append(float(r["accuracy"]))
    import statistics
    for m in ("ZY-BERT", "InternLM3"):
        mu = sum(seeds[m]) / 3
        sd = statistics.stdev(seeds[m])
        print(f"{m}: mean {mu:.2f} sd {sd:.2f}")

    print("\n== SVG text checks ==")
    checks = {
        "Figure1.svg": ["75.77", "66.51", "69.58", "60.74", "+6.19 pp", "+5.77 pp",
                        "74.92 \u00b1 1.13", "69.42 \u00b1 0.21", "4,218", "4,186", "860", "6"],
        "Figure5.svg": ["75.77", "66.51", "69.58", "60.74", "62.78", "56.81",
                        "58.70", "54.50", "+6.19 pp", "4.93", "7.44", "505 / 244"],
        "Figure6.svg": ["75.77", "75.34", "73.64", "69.58", "69.49", "69.18",
                        "74.92 \u00b1 1.13", "69.42 \u00b1 0.21"],
        "Figure7.svg": ["860", "6", "support"],
        "Figure8.svg": ["99.95", "100.00", "77", "92", "136"],
    }
    for fig, needles in checks.items():
        miss = check_svg(fig, needles)
        print(f"{fig}: {len(needles) - len(miss)}/{len(needles)} strings present")
        if miss:
            fails.append(f"{fig} missing {miss}")

    print("\n== result ==")
    if fails:
        for f in fails:
            print("FAIL:", f)
        return 1
    print("PASS: all recomputed metrics match the archived tables; all SVG strings present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
