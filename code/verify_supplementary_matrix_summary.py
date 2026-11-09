#!/usr/bin/env python3
"""Verify the public Supplementary Figure S1-S4 matrix summary and top-10 errors.

Uses only public aggregate CSV/JSON files. It does not read clinical records,
case-level predictions, or model checkpoints.
Run from the repository root:
    python code/verify_supplementary_matrix_summary.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "figures_py" / "source_data"

MODELS = {
    "ZY-BERT": ("confusion_matrix_zybert.csv", 4218, 3196, "ZY-BERT"),
    "InternLM3-8B": ("confusion_matrix_internlm3.csv", 4216, 2935, "InternLM3"),
    "MacBERT": ("confusion_matrix_macbert.csv", 4218, 2648, "MacBERT"),
    "Qwen3-8B": ("confusion_matrix_qwen3.csv", 4216, 2476, "Qwen3"),
}


def read_matrix(filename: str, labels: list[str]) -> tuple[list[str], list[list[int]]]:
    with (DATA / filename).open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        raise ValueError(f"{filename}: empty CSV")
    columns = [x.strip() for x in rows[0][1:]]
    row_labels = [r[0].strip() for r in rows[1:]]
    if columns != labels or row_labels != labels:
        raise AssertionError(f"{filename}: label order differs from syndrome_label_list.json")
    matrix = []
    for row in rows[1:]:
        values = [int(float(x)) for x in row[1:]]
        if len(values) != len(labels) or any(v < 0 for v in values):
            raise AssertionError(f"{filename}: invalid matrix row")
        matrix.append(values)
    if len(matrix) != len(labels):
        raise AssertionError(f"{filename}: expected {len(labels)} rows")
    return row_labels, matrix


def main() -> int:
    labels = json.loads((DATA / "syndrome_label_list.json").read_text(encoding="utf-8"))
    if len(labels) != 42 or len(set(labels)) != 42:
        raise AssertionError("expected 42 unique frozen labels")
    id_to_index = {f"C{i + 1:02d}": i for i in range(len(labels))}

    with (DATA / "classwise_metrics.csv").open(encoding="utf-8-sig", newline="") as fh:
        support = {r["label"]: int(r["support"]) for r in csv.DictReader(fh)}
    if set(support) != set(labels) or sum(support.values()) != 4218:
        raise AssertionError("classwise support does not reconcile to N=4,218")

    matrices = {}
    for model, (filename, expected_n, expected_correct, _) in MODELS.items():
        row_labels, matrix = read_matrix(filename, labels)
        matrix_n = sum(sum(row) for row in matrix)
        correct = sum(matrix[i][i] for i in range(len(labels)))
        offdiag = matrix_n - correct
        if (matrix_n, correct) != (expected_n, expected_correct):
            raise AssertionError(
                f"{model}: got matrix_n={matrix_n}, correct={correct}; "
                f"expected {expected_n}, {expected_correct}"
            )
        matrices[model] = matrix

    with (DATA / "fig8_errors.csv").open(encoding="utf-8-sig", newline="") as fh:
        error_rows = list(csv.DictReader(fh))
    if len(error_rows) != 10:
        raise AssertionError(f"expected 10 error directions, found {len(error_rows)}")

    top10 = {model: 0 for model in MODELS}
    for expected_rank, row in enumerate(error_rows, start=1):
        if int(row["rank"]) != expected_rank:
            raise AssertionError("top-10 error rows are not in rank order")
        true_id, pred_id = row["true_id"], row["pred_id"]
        if true_id not in id_to_index or pred_id not in id_to_index:
            raise AssertionError(f"unknown label ID in row {expected_rank}")
        ti, pi = id_to_index[true_id], id_to_index[pred_id]
        for model, (_, _, _, csv_field) in MODELS.items():
            actual = matrices[model][ti][pi]
            reported = int(row[csv_field])
            if actual != reported:
                raise AssertionError(
                    f"{model} {true_id}->{pred_id}: CSV={reported}, matrix={actual}"
                )
            top10[model] += reported

    print("\nVerified top-10 summary (denominator = valid-label off-diagonal errors):")
    print("model,valid_matrix_n,correct,off_diagonal_errors,top10_errors,top10_pct_of_off_diagonal")
    for model, (_, matrix_n, correct, _) in MODELS.items():
        offdiag = matrix_n - correct
        count = top10[model]
        pct = 100.0 * count / offdiag if offdiag else 0.0
        print(f"{model}: top10={count}; offdiag={offdiag}; share={pct:.1f}%")
    print("\nPASS: all 40 top-10 cells match the four public confusion matrices.")
    print("Note: empty generative outputs are outside the 42x42 matrices and remain errors in N=4,218 metrics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
