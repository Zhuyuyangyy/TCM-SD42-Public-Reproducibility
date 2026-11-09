#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate and validate Supplementary Figures S0-S4 from public aggregates.

The script reads only the public frozen confusion matrices and aggregate
support/error-direction tables. It does not use clinical records, case-level
predictions, or model checkpoints.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = HERE / "source_data"
DEFAULT_OUT = HERE / "supp_figures"
N_TEST = 4218

SYSTEMS = [
    {
        "key": "zybert", "tag": "S1", "name": "ZY-BERT", "field": "ZY-BERT",
        "color": "#0072B2", "valid_n": 4218, "correct": 3196, "top10": 324,
        "share": 31.7, "blob_sha1": "6f46385b011a10a8195e038f97f1608d13f163a4",
    },
    {
        "key": "internlm3", "tag": "S2", "name": "InternLM3-8B", "field": "InternLM3",
        "color": "#D55E00", "valid_n": 4216, "correct": 2935, "top10": 409,
        "share": 31.9, "blob_sha1": "048328739b492ca419903a91a7e104165f91530d",
    },
    {
        "key": "macbert", "tag": "S3", "name": "MacBERT", "field": "MacBERT",
        "color": "#009E73", "valid_n": 4218, "correct": 2648, "top10": 640,
        "share": 40.8, "blob_sha1": "e6a848b1081bcd125a8011878ae5faa3466177ba",
    },
    {
        "key": "qwen3", "tag": "S4", "name": "Qwen3-8B", "field": "Qwen3",
        "color": "#CC79A7", "valid_n": 4216, "correct": 2476, "top10": 667,
        "share": 38.3, "blob_sha1": "0516279254e6c3b0f1b030f584e735ca1e463cad",
    },
]
NAVY = "#1F3864"
ORANGE = "#C55A11"
TEAL = "#1E6F77"
LIGHT = "#DCE6F0"


def git_blob_sha1(path: Path) -> str:
    """Return the Git blob object SHA-1 for a file, including the blob header."""
    payload = path.read_bytes()
    header = f"blob {len(payload)}\\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def load_labels() -> list[str]:
    labels_path = ROOT / "code" / "labels_42.txt"
    labels = [line.strip() for line in labels_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(labels) != 42 or len(set(labels)) != 42:
        raise AssertionError("code/labels_42.txt must contain 42 unique frozen labels")
    return labels


def load_support(labels: list[str]) -> dict[str, int]:
    path = SOURCE / "classwise_metrics.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    support = {row["label"]: int(row["support"]) for row in rows}
    if set(support) != set(labels) or sum(support.values()) != N_TEST:
        raise AssertionError("classwise_metrics.csv support must reconcile to N=4,218")
    return support


def load_matrix(key: str, labels: list[str]) -> np.ndarray:
    path = ROOT / "results" / f"confusion_matrix_{key}.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows or rows[0][0] != "gold\\\\pred":
        raise AssertionError(f"{path.name}: unexpected matrix header")
    columns = [value.strip() for value in rows[0][1:]]
    row_labels = [row[0].strip() for row in rows[1:]]
    if columns != labels or row_labels != labels:
        raise AssertionError(f"{path.name}: row/column order differs from frozen 42-label order")
    matrix = np.asarray([[int(value) for value in row[1:]] for row in rows[1:]], dtype=np.int64)
    if matrix.shape != (42, 42) or np.any(matrix < 0):
        raise AssertionError(f"{path.name}: expected a non-negative 42x42 matrix")
    expected_sha = next(spec["blob_sha1"] for spec in SYSTEMS if spec["key"] == key)
    actual_sha = git_blob_sha1(path)
    if actual_sha != expected_sha:
        raise AssertionError(f"{path.name}: Git blob SHA-1 {actual_sha} != frozen {expected_sha}")
    return matrix


def validate_inputs():
    """Validate matrix provenance, support accounting, and all 40 top-10 cells."""
    labels = load_labels()
    support = load_support(labels)
    matrices = {}
    summary = {}
    id_to_index = {f"C{i + 1:02d}": i for i in range(42)}

    for spec in SYSTEMS:
        matrix = load_matrix(spec["key"], labels)
        valid_n = int(matrix.sum())
        correct = int(np.trace(matrix))
        if (valid_n, correct) != (spec["valid_n"], spec["correct"]):
            raise AssertionError(
                f"{spec['name']}: matrix total/correct {(valid_n, correct)} "
                f"!= expected {(spec['valid_n'], spec['correct'])}"
            )
        row_sums = matrix.sum(axis=1)
        gold_support = np.asarray([support[label] for label in labels])
        if np.any(row_sums <= 0) or np.any(row_sums > gold_support):
            raise AssertionError(f"{spec['name']}: invalid row support")
        omitted = int(np.sum(gold_support - row_sums))
        expected_omitted = N_TEST - valid_n
        if omitted != expected_omitted or omitted not in (0, 2):
            raise AssertionError(f"{spec['name']}: row support does not explain {expected_omitted} omitted outputs")
        matrices[spec["key"]] = matrix
        summary[spec["key"]] = {
            "valid_n": valid_n,
            "correct": correct,
            "off_diagonal": valid_n - correct,
            "omitted": omitted,
        }

    error_path = SOURCE / "fig8_errors.csv"
    with error_path.open(encoding="utf-8-sig", newline="") as handle:
        error_rows = list(csv.DictReader(handle))
    if len(error_rows) != 10:
        raise AssertionError(f"fig8_errors.csv must contain 10 rows, found {len(error_rows)}")

    top10 = {spec["key"]: 0 for spec in SYSTEMS}
    for expected_rank, row in enumerate(error_rows, start=1):
        if int(row["rank"]) != expected_rank:
            raise AssertionError("fig8_errors.csv must be ordered by ranks 1-10")
        true_id, pred_id = row["true_id"], row["pred_id"]
        if true_id not in id_to_index or pred_id not in id_to_index:
            raise AssertionError(f"unknown frozen label ID in top-10 row {expected_rank}")
        ti, pi = id_to_index[true_id], id_to_index[pred_id]
        for spec in SYSTEMS:
            observed = int(matrices[spec["key"]][ti, pi])
            reported = int(row[spec["field"]])
            if observed != reported:
                raise AssertionError(
                    f"{spec['name']} {true_id}->{pred_id}: matrix={observed}, top-10 CSV={reported}"
                )
            top10[spec["key"]] += reported

    for spec in SYSTEMS:
        key = spec["key"]
        if top10[key] != spec["top10"]:
            raise AssertionError(f"{spec['name']}: top-10 sum {top10[key]} != {spec['top10']}")
        share = 100.0 * top10[key] / summary[key]["off_diagonal"]
        if round(share, 1) != spec["share"]:
            raise AssertionError(f"{spec['name']}: top-10 share {share:.3f}% != {spec['share']:.1f}%")
        summary[key]["top10"] = top10[key]
        summary[key]["top10_share"] = share

    return matrices, error_rows, summary


def fig_s0(mats, error_rows, summary, out_dir: Path, dpi: int):
    names = [spec["name"] for spec in SYSTEMS]
    keys = [spec["key"] for spec in SYSTEMS]
    diag = [summary[key]["correct"] for key in keys]
    off = [summary[key]["off_diagonal"] for key in keys]
    t10 = [summary[key]["top10"] for key in keys]

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(12.6, 5.4), gridspec_kw={"width_ratios": [1, 1]}
    )
    x = np.arange(4)
    width = 0.34
    bars_correct = ax1.bar(x - width / 2, diag, width, color=NAVY,
                           label="Diagonal (Correct predictions)")
    bars_error = ax1.bar(x + width / 2, off, width, color=ORANGE,
                         label="Off-diagonal (Misclassifications)")
    for bars in (bars_correct, bars_error):
        for bar in bars:
            ax1.annotate(
                f"{int(bar.get_height()):,}",
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                textcoords="offset points", xytext=(0, 3), ha="center",
                fontsize=10, color=NAVY,
            )
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, fontsize=11, fontweight="bold")
    ax1.set_ylabel("Number of valid class-valued\\npredictions (out of N = 4,218)", fontsize=10)
    ax1.set_ylim(0, 3500)
    ax1.grid(axis="y", color="#E6E6E6")
    ax1.set_axisbelow(True)
    for spine in ("top", "right"):
        ax1.spines[spine].set_visible(False)
    ax1.legend(frameon=False, fontsize=9, loc="upper right")
    ax1.set_title("(a)", loc="left", fontsize=15, fontweight="bold")

    rest = [off[i] - t10[i] for i in range(4)]
    ax2.bar(x, t10, 0.55, color=TEAL, label="Top 10 confusion directions (Table S3)")
    ax2.bar(x, rest, 0.55, bottom=t10, color=LIGHT,
            label="Remaining off-diagonal errors")
    for i in range(4):
        ax2.annotate(
            f"Total: {off[i]:,}", (x[i], off[i]), textcoords="offset points",
            xytext=(0, 6), ha="center", fontsize=10, fontweight="bold", color="#222222",
        )
        ax2.annotate(
            f"{t10[i]}\\n{100 * t10[i] / off[i]:.1f}%", (x[i], t10[i] / 2),
            ha="center", va="center", fontsize=9, color="white", fontweight="bold",
        )
    ax2.set_xticks(x)
    ax2.set_xticklabels(names, fontsize=11, fontweight="bold")
    ax2.set_ylabel("Off-diagonal misclassified cases", fontsize=10)
    ax2.set_ylim(0, 2050)
    ax2.grid(axis="y", color="#E6E6E6")
    ax2.set_axisbelow(True)
    for spine in ("top", "right"):
        ax2.spines[spine].set_visible(False)
    ax2.legend(frameon=False, fontsize=9, loc="upper left")
    ax2.set_title("(b)", loc="left", fontsize=15, fontweight="bold")

    fig.text(
        0.08, 0.02,
        "Counts cover valid class-valued off-diagonal errors only. Two empty outputs per generative model lie outside "
        "the 42 x 42 grid. Percentages = top-10 sum / model off-diagonal total (1,022 / 1,281 / 1,570 / 1,740).",
        fontsize=8.5, color="#444444",
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    for extension in ("png", "svg"):
        fig.savefig(out_dir / f"FigureS0.{extension}", dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def fig_heatmap(key, tag, name, matrix, out_dir: Path, dpi: int):
    row_sums = matrix.sum(axis=1, keepdims=True)
    share = np.divide(matrix * 100.0, row_sums, out=np.zeros_like(matrix, dtype=float), where=row_sums > 0)
    total = int(matrix.sum())
    correct = int(np.trace(matrix))

    fig, ax = plt.subplots(figsize=(7.4, 7.6))
    im = ax.imshow(share, cmap="Blues", vmin=0, vmax=100, interpolation="nearest")
    ticks = list(range(0, 42, 2))
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xticklabels([str(t + 1) for t in ticks], fontsize=8)
    ax.set_yticklabels([str(t + 1) for t in ticks], fontsize=8)
    ax.set_xlabel("Predicted class ID (see Supplementary Table S4)", fontsize=10)
    ax.set_ylabel("Gold class ID (see Supplementary Table S4)", fontsize=10)
    colorbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.03)
    colorbar.set_label("Within-row share of valid predictions (%)", fontsize=9)

    fig.text(0.08, 0.95, f"Supplementary Figure {tag}  |  {name}",
             fontsize=15, fontweight="bold", color="#222222")
    fig.text(
        0.08, 0.915,
        f"42 x 42 clean held-out confusion matrix  |  {correct:,} correct / {total:,} class-valued outputs",
        fontsize=9.5, color="#555555",
    )
    omitted = N_TEST - total
    note = (
        f"All {total:,} outputs have a valid class ID."
        if omitted == 0
        else f"{total:,} outputs have a valid class ID; the two empty outputs of this model lie outside the matrix."
    )
    fig.text(
        0.08, 0.055,
        f"Source: public frozen confusion_matrix_{key}.csv; archived Git blob SHA-1 verified.",
        fontsize=8, color="#666666",
    )
    fig.text(0.08, 0.035, note, fontsize=8, color="#666666")
    fig.text(
        0.08, 0.015,
        "Rows sum to 100% among class-valued outputs, not necessarily all gold cases.",
        fontsize=8, color="#666666",
    )
    fig.subplots_adjust(left=0.11, right=0.86, top=0.88, bottom=0.12)
    for extension in ("png", "svg"):
        fig.savefig(out_dir / f"Figure{tag}.{extension}", dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def generate_all(out_dir: Path, dpi: int = 300):
    mats, error_rows, summary = validate_inputs()
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_s0(mats, error_rows, summary, out_dir, dpi)
    for spec in SYSTEMS:
        fig_heatmap(spec["key"], spec["tag"], spec["name"], mats[spec["key"]], out_dir, dpi)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()
    if args.dpi < 72:
        parser.error("--dpi must be at least 72")
    summary = generate_all(args.output_dir, args.dpi)
    for spec in SYSTEMS:
        row = summary[spec["key"]]
        print(
            f"{spec['name']}: valid={row['valid_n']}, correct={row['correct']}, "
            f"offdiag={row['off_diagonal']}, top10={row['top10']} ({row['top10_share']:.1f}%)"
        )
    print(f"PASS: S0-S4 regenerated and validated in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
