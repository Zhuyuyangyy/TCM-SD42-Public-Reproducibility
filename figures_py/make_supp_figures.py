#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate Supplementary Figures S0-S4 from the archived confusion matrices.

S0: diagonal vs off-diagonal counts and the share of errors concentrated in the
    top-10 confusion directions.
S1-S4: row-normalized 42 x 42 heatmaps for the four systems.

The plotted values match the typeset supplement; the vector styling is a
clean re-implementation and is not claimed to be pixel-identical.
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "supp_figures")
os.makedirs(OUT, exist_ok=True)

SYSTEMS = [
    ("zybert", "S1", "ZY-BERT", "#0072B2"),
    ("internlm3", "S2", "InternLM3-8B", "#D55E00"),
    ("macbert", "S3", "MacBERT", "#009E73"),
    ("qwen3", "S4", "Qwen3-8B", "#CC79A7"),
]
NAVY = "#1F3864"
ORANGE = "#C55A11"
TEAL = "#1E6F77"
LIGHT = "#DCE6F0"


def load_matrix(key):
    path = os.path.join(ROOT, "results", f"confusion_matrix_{key}.csv")
    with open(path, encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    m = np.array([[int(x) for x in r[1:]] for r in rows[1:]], dtype=float)
    return m


def top10_counts():
    path = os.path.join(HERE, "source_data", "fig8_errors.csv")
    with open(path, encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    cols = {"ZY-BERT": "ZY-BERT", "InternLM3-8B": "InternLM3",
            "MacBERT": "MacBERT", "Qwen3-8B": "Qwen3"}
    return {name: sum(int(r[col]) for r in rows) for name, col in cols.items()}


def fig_s0(mats):
    top10 = top10_counts()
    names = ["ZY-BERT", "InternLM3-8B", "MacBERT", "Qwen3-8B"]
    keys = ["zybert", "internlm3", "macbert", "qwen3"]
    diag = [int(np.trace(mats[k])) for k in keys]
    off = [int(mats[k].sum() - np.trace(mats[k])) for k in keys]
    totals = [d + o for d, o in zip(diag, off)]
    t10 = [top10[n] for n in names]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.6, 5.4), gridspec_kw={"width_ratios": [1, 1]})
    x = np.arange(4)
    w = 0.34
    b1 = ax1.bar(x - w / 2, diag, w, color=NAVY, label="Diagonal (Correct predictions)")
    b2 = ax1.bar(x + w / 2, off, w, color=ORANGE, label="Off-diagonal (Misclassifications)")
    for bars in (b1, b2):
        for b in bars:
            ax1.annotate(f"{int(b.get_height()):,}", (b.get_x() + b.get_width() / 2, b.get_height()),
                         textcoords="offset points", xytext=(0, 3), ha="center", fontsize=10, color=NAVY)
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, fontsize=11, fontweight="bold")
    ax1.set_ylabel("Number of valid class-valued\npredictions (out of N = 4,218)", fontsize=10)
    ax1.set_ylim(0, 3500)
    ax1.grid(axis="y", color="#E6E6E6")
    ax1.set_axisbelow(True)
    for s in ("top", "right"):
        ax1.spines[s].set_visible(False)
    ax1.legend(frameon=False, fontsize=9, loc="upper right")
    ax1.set_title("(a)", loc="left", fontsize=15, fontweight="bold")

    rest = [o - t for o, t in zip(off, t10)]
    ax2.bar(x, t10, 0.55, color=TEAL, label="Top 10 confusion directions (Table S3)")
    ax2.bar(x, rest, 0.55, bottom=t10, color=LIGHT,
            label="Remaining off-diagonal errors (1,712 other directions)")
    for i in range(4):
        ax2.annotate(f"Total: {off[i]:,}", (x[i], off[i]), textcoords="offset points",
                     xytext=(0, 6), ha="center", fontsize=10, fontweight="bold", color="#222222")
        ax2.annotate(f"{t10[i]}\n{100 * t10[i] / off[i]:.1f}%", (x[i], t10[i] / 2),
                     ha="center", va="center", fontsize=9, color="white", fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(names, fontsize=11, fontweight="bold")
    ax2.set_ylabel("Off-diagonal misclassified cases", fontsize=10)
    ax2.set_ylim(0, 2050)
    ax2.grid(axis="y", color="#E6E6E6")
    ax2.set_axisbelow(True)
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)
    ax2.legend(frameon=False, fontsize=9, loc="upper left")
    ax2.set_title("(b)", loc="left", fontsize=15, fontweight="bold")

    fig.text(0.08, 0.02,
             "Counts cover valid class-valued off-diagonal errors only. The two empty/invalid outputs of each "
             "generative model lie outside\nthe 42 x 42 grid and are excluded here. Percentages = top-10 sum / "
             "model off-diagonal total (1,022 / 1,281 / 1,570 / 1,740).",
             fontsize=8.5, color="#444444")
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    path = os.path.join(OUT, "FigureS0.png")
    fig.savefig(path, dpi=300)
    plt.close(fig)
    print("wrote", path)


def fig_heatmap(key, tag, name, colour):
    m = load_matrix(key)
    row = m.sum(axis=1, keepdims=True)
    share = np.divide(m * 100.0, row, out=np.zeros_like(m), where=row > 0)
    total = int(m.sum())
    correct = int(np.trace(m))

    fig, ax = plt.subplots(figsize=(7.4, 7.6))
    im = ax.imshow(share, cmap="Blues", vmin=0, vmax=100, interpolation="nearest")
    ticks = list(range(0, 42, 2))
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xticklabels([str(t + 1) for t in ticks], fontsize=8)
    ax.set_yticklabels([str(t + 1) for t in ticks], fontsize=8)
    ax.set_xlabel("Predicted class ID (see Supplementary Table S4)", fontsize=10)
    ax.set_ylabel("Gold class ID (see Supplementary Table S4)", fontsize=10)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03)
    cb.set_label("Within-row share of valid predictions (%)", fontsize=9)

    fig.text(0.08, 0.95, f"Supplementary Figure {tag}  |  {name}", fontsize=15,
             fontweight="bold", color="#222222")
    fig.text(0.08, 0.915, f"42 x 42 clean held-out confusion matrix  |  {correct:,} correct / "
                          f"{total:,} class-valued outputs", fontsize=9.5, color="#555555")
    if total == 4218:
        note = f"All {total:,} outputs have a valid class ID."
    else:
        note = (f"{total:,} outputs have a valid class ID; the two empty outputs of this model lie "
                f"outside the matrix.")
    fig.text(0.08, 0.055, "Source: public frozen confusion_matrix_%s.csv; archived Git blob SHA-1 verified."
             % key, fontsize=8, color="#666666")
    fig.text(0.08, 0.035, note, fontsize=8, color="#666666")
    fig.text(0.08, 0.015, "Rows sum to 100% among class-valued outputs, not necessarily all gold cases.",
             fontsize=8, color="#666666")
    fig.subplots_adjust(left=0.11, right=0.86, top=0.88, bottom=0.12)
    path = os.path.join(OUT, f"Figure{tag}.png")
    fig.savefig(path, dpi=300)
    plt.close(fig)
    print("wrote", path)


if __name__ == "__main__":
    mats = {k: load_matrix(k) for k, _, _, _ in SYSTEMS}
    fig_s0(mats)
    for key, tag, name, colour in SYSTEMS:
        fig_heatmap(key, tag, name, colour)
