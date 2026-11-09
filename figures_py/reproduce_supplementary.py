#!/usr/bin/env python3
"""Rebuild Supplementary Figures S0-S4 from public aggregate source files.

No clinical records, case-level predictions, or model checkpoints are used.
Run from the repository root:
    python figures_py/reproduce_supplementary.py
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source_data"
DEFAULT_OUTPUT = HERE / "generated_supplementary"
N_TEST = 4218

MODELS = [
    {"name": "ZY-BERT", "slug": "zybert", "matrix": "confusion_matrix_zybert.csv",
     "error_field": "ZY-BERT", "valid_n": 4218, "correct": 3196, "top10": 324,
     "share": 31.7, "color": "#0072B2"},
    {"name": "InternLM3-8B", "slug": "internlm3", "matrix": "confusion_matrix_internlm3.csv",
     "error_field": "InternLM3", "valid_n": 4216, "correct": 2935, "top10": 409,
     "share": 31.9, "color": "#D55E00"},
    {"name": "MacBERT", "slug": "macbert", "matrix": "confusion_matrix_macbert.csv",
     "error_field": "MacBERT", "valid_n": 4218, "correct": 2648, "top10": 640,
     "share": 40.8, "color": "#009E73"},
    {"name": "Qwen3-8B", "slug": "qwen3", "matrix": "confusion_matrix_qwen3.csv",
     "error_field": "Qwen3", "valid_n": 4216, "correct": 2476, "top10": 667,
     "share": 38.3, "color": "#CC79A7"},
]

OUTCOME_COLORS = {"correct": "#009E73", "valid_error": "#D55E00", "empty": "#999999"}


def _read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.reader(handle))


def load_inputs():
    """Load and strictly validate all aggregate inputs before drawing."""
    labels = json.loads((SOURCE / "syndrome_label_list.json").read_text(encoding="utf-8"))
    if len(labels) != 42 or len(set(labels)) != 42:
        raise AssertionError("syndrome_label_list.json must contain 42 unique labels")
    id_to_index = {f"C{i + 1:02d}": i for i in range(42)}

    with (SOURCE / "classwise_metrics.csv").open(encoding="utf-8-sig", newline="") as handle:
        support_rows = list(csv.DictReader(handle))
    support = {row["label"]: int(row["support"]) for row in support_rows}
    if set(support) != set(labels) or sum(support.values()) != N_TEST:
        raise AssertionError("classwise support must reconcile to N=4,218")

    matrices = {}
    summaries = {}
    for spec in MODELS:
        rows = _read_csv(SOURCE / spec["matrix"])
        if not rows or rows[0][0] != "gold\\pred":
            raise AssertionError(f"{spec['matrix']}: unexpected CSV header")
        columns = [x.strip() for x in rows[0][1:]]
        row_labels = [row[0].strip() for row in rows[1:]]
        if columns != labels or row_labels != labels:
            raise AssertionError(f"{spec['matrix']}: label order differs from frozen vocabulary")
        matrix = np.asarray([[int(x) for x in row[1:]] for row in rows[1:]], dtype=np.int64)
        if matrix.shape != (42, 42) or np.any(matrix < 0):
            raise AssertionError(f"{spec['matrix']}: expected a non-negative 42x42 matrix")
        row_sums = matrix.sum(axis=1)
        expected_support = np.asarray([support[x] for x in labels])
        if np.any(row_sums <= 0) or np.any(row_sums > expected_support):
            raise AssertionError(f"{spec['matrix']}: invalid row support")
        valid_n = int(matrix.sum())
        correct = int(np.trace(matrix))
        if valid_n != spec["valid_n"] or correct != spec["correct"]:
            raise AssertionError(
                f"{spec['name']}: matrix N/correct {(valid_n, correct)} "
                f"!= expected {(spec['valid_n'], spec['correct'])}"
            )
        omitted = N_TEST - valid_n
        if omitted not in (0, 2):
            raise AssertionError(f"{spec['name']}: unexpected omitted-output count {omitted}")
        if int(np.sum(expected_support - row_sums)) != omitted:
            raise AssertionError(f"{spec['name']}: row supports do not explain omitted outputs")
        matrices[spec["name"]] = matrix
        summaries[spec["name"]] = {
            "valid_n": valid_n,
            "correct": correct,
            "valid_errors": valid_n - correct,
            "empty": omitted,
            "off_diagonal": valid_n - correct,
        }

    with (SOURCE / "fig8_errors.csv").open(encoding="utf-8-sig", newline="") as handle:
        error_rows = list(csv.DictReader(handle))
    if len(error_rows) != 10:
        raise AssertionError(f"fig8_errors.csv must contain 10 rows, found {len(error_rows)}")

    top10_counts = {spec["name"]: 0 for spec in MODELS}
    for expected_rank, row in enumerate(error_rows, start=1):
        if int(row["rank"]) != expected_rank:
            raise AssertionError("fig8_errors.csv is not ordered by rank 1-10")
        true_id, pred_id = row["true_id"], row["pred_id"]
        if true_id not in id_to_index or pred_id not in id_to_index:
            raise AssertionError(f"unknown frozen label ID in top-10 row {expected_rank}")
        ti, pi = id_to_index[true_id], id_to_index[pred_id]
        for spec in MODELS:
            actual = int(matrices[spec["name"]][ti, pi])
            reported = int(row[spec["error_field"]])
            if actual != reported:
                raise AssertionError(
                    f"{spec['name']} {true_id}->{pred_id}: matrix={actual}, CSV={reported}"
                )
            top10_counts[spec["name"]] += reported

    for spec in MODELS:
        name = spec["name"]
        summary = summaries[name]
        count = top10_counts[name]
        share = 100.0 * count / summary["off_diagonal"]
        if count != spec["top10"] or round(share, 1) != spec["share"]:
            raise AssertionError(
                f"{name}: top-10 count/share {(count, round(share, 1))} "
                f"!= expected {(spec['top10'], spec['share'])}"
            )
        summary["top10"] = count
        summary["top10_share"] = share

    return labels, matrices, error_rows, summaries


def plot_s0(error_rows, summaries, output_dir: Path, dpi: int):
    """Two-panel overview: full outcome accounting and top-10 pooled directions."""
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    fig, (ax_a, ax_b) = plt.subplots(
        1, 2, figsize=(16, 8), gridspec_kw={"width_ratios": [1.0, 1.45]}
    )
    fig.suptitle(
        "Supplementary Figure S0. Confusion-matrix summary and recurrent error directions",
        fontsize=14, fontweight="bold", y=0.98,
    )

    names = [spec["name"] for spec in MODELS]
    y = np.arange(len(names))
    correct = [summaries[name]["correct"] for name in names]
    valid_errors = [summaries[name]["valid_errors"] for name in names]
    empty = [summaries[name]["empty"] for name in names]

    ax_a.barh(y, correct, color=OUTCOME_COLORS["correct"], label="Correct")
    ax_a.barh(y, valid_errors, left=correct, color=OUTCOME_COLORS["valid_error"],
              label="Valid-label errors")
    left_empty = [correct[i] + valid_errors[i] for i in range(len(names))]
    ax_a.barh(y, empty, left=left_empty, color=OUTCOME_COLORS["empty"], label="Empty outputs")
    ax_a.set_yticks(y, names)
    ax_a.invert_yaxis()
    ax_a.set_xlim(0, 4550)
    ax_a.set_xticks([0, 1000, 2000, 3000, 4000])
    ax_a.set_xlabel("Records (fixed denominator N = 4,218)")
    ax_a.set_title("A  Held-out outcome accounting", loc="left", fontweight="bold")
    ax_a.grid(axis="x", color="#DDDDDD", linewidth=0.6)
    ax_a.set_axisbelow(True)
    for i in range(len(names)):
        ax_a.text(correct[i] / 2, i, f"{correct[i]:,}", va="center", ha="center",
                  color="white", fontsize=8, fontweight="bold")
        if valid_errors[i] > 100:
            ax_a.text(correct[i] + valid_errors[i] / 2, i, f"{valid_errors[i]:,}",
                      va="center", ha="center", color="white", fontsize=8)
        if empty[i]:
            ax_a.text(left_empty[i] + 24, i, f"{empty[i]} empty", va="center",
                      ha="left", color="#555555", fontsize=8)
    ax_a.legend(loc="lower right", frameon=False, fontsize=8)

    y2 = np.arange(len(error_rows))
    left = np.zeros(len(error_rows), dtype=float)
    direction_labels = [
        f"{int(row['rank']):02d}. {row['true_id']} -> {row['pred_id']}" for row in error_rows
    ]
    pooled = np.zeros(len(error_rows), dtype=int)
    for spec in MODELS:
        vals = np.asarray([int(row[spec["error_field"]]) for row in error_rows], dtype=int)
        ax_b.barh(y2, vals, left=left, color=spec["color"], label=spec["name"], height=0.72)
        for i, value in enumerate(vals):
            if value >= 18:
                ax_b.text(left[i] + value / 2, i, str(value), ha="center", va="center",
                          fontsize=7, color="white", fontweight="bold")
        left += vals
        pooled += vals
    ax_b.set_yticks(y2, direction_labels)
    ax_b.invert_yaxis()
    ax_b.set_xlabel("Model-record errors (pooled across four systems)")
    ax_b.set_title("B  Top-10 off-diagonal confusion directions", loc="left", fontweight="bold")
    ax_b.grid(axis="x", color="#DDDDDD", linewidth=0.6)
    ax_b.set_axisbelow(True)
    ax_b.set_xlim(0, max(pooled) * 1.16)
    for i, value in enumerate(pooled):
        ax_b.text(value + max(pooled) * 0.015, i, f"{value:,}", va="center", fontsize=8)
    ax_b.legend(loc="lower right", frameon=False, fontsize=8, ncol=2)

    fig.text(
        0.01, 0.015,
        "Two empty outputs per generative model are excluded from 42x42 matrices but remain errors in the full N=4,218 evaluation.",
        fontsize=8, color="#555555",
    )
    fig.tight_layout(rect=(0, 0.045, 1, 0.94))
    for ext in ("png", "svg"):
        fig.savefig(output_dir / f"FigureS0.{ext}", dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def plot_heatmap(model_name: str, matrix: np.ndarray, figure_no: int,
                 output_dir: Path, dpi: int):
    """Draw one row-normalized 42x42 matrix; denominators are valid outputs per gold row."""
    row_sums = matrix.sum(axis=1)
    pct = matrix / row_sums[:, None] * 100.0
    tick_labels = [f"C{i:02d}" for i in range(1, 43)]

    fig, ax = plt.subplots(figsize=(13.5, 12.5))
    im = ax.imshow(pct, cmap="YlOrRd", vmin=0, vmax=100, interpolation="nearest", aspect="equal")
    ax.set_xticks(np.arange(42), tick_labels, rotation=90, fontsize=7)
    ax.set_yticks(np.arange(42), tick_labels, fontsize=7)
    ax.set_xlabel("Predicted frozen label ID", labelpad=10)
    ax.set_ylabel("Gold frozen label ID", labelpad=10)
    ax.set_title(
        f"Supplementary Figure S{figure_no}. {model_name}: row-normalized 42x42 confusion matrix",
        fontsize=13, fontweight="bold", pad=14,
    )
    colorbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    colorbar.set_label("Row-normalized count (%)")
    fig.text(
        0.5, 0.018,
        "Rows are normalized over valid class-valued outputs only. Empty outputs are excluded from the grid and counted as errors in N=4,218.",
        ha="center", fontsize=8, color="#555555",
    )
    fig.tight_layout(rect=(0.02, 0.045, 0.96, 0.97))
    slug = MODELS[figure_no - 1]["slug"]
    for ext in ("png", "svg"):
        fig.savefig(output_dir / f"FigureS{figure_no}_{slug}.{ext}", dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def generate_all(output_dir: Path, dpi: int = 300):
    _, matrices, error_rows, summaries = load_inputs()
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_s0(error_rows, summaries, output_dir, dpi)
    for figure_no, spec in enumerate(MODELS, start=1):
        plot_heatmap(spec["name"], matrices[spec["name"]], figure_no, output_dir, dpi)
    return summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()
    if args.dpi < 72:
        parser.error("--dpi must be at least 72")
    summaries = generate_all(args.output_dir, dpi=args.dpi)
    print("Supplementary figures generated:")
    for spec in MODELS:
        summary = summaries[spec["name"]]
        print(
            f"{spec['name']}: valid_n={summary['valid_n']}, correct={summary['correct']}, "
            f"top10={summary['top10']} ({summary['top10_share']:.1f}%)"
        )
    print(f"Output directory: {args.output_dir.resolve()}")
    print("PASS: S0 and S1-S4 were generated from the public aggregate source files.")


if __name__ == "__main__":
    main()
