#!/usr/bin/env python3
"""Checks for the final publication-facing figure source tables and semantics."""
from __future__ import annotations

import csv
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "figures_py" / "source_data"


class FinalFigureSourceTests(unittest.TestCase):
    def test_dedup_values_are_from_results_table(self):
        with (SOURCE / "fig6_dedup.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        row = next(r for r in rows if r["pair"] == "MacBERT vs Qwen3")
        self.assertEqual(row["S1"], "4.11")
        self.assertEqual(row["S1_source"], "results/dedup_sensitivity_seed42.csv")

    def test_balanced_accuracy_sources_are_split_by_method_and_full_precision(self):
        with (SOURCE / "fig6_bootstrap.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        mf1 = {r["pair"]: r for r in rows if r["metric"] == "Macro-F1"}
        ba = {r["pair"]: r for r in rows if r["metric"] == "Balanced accuracy"}
        self.assertEqual(mf1["ZY-BERT vs InternLM3"]["ord_source"], "results/pairwise_macro_f1_bootstrap_seed42.csv")
        self.assertEqual((ba["ZY-BERT vs MacBERT"]["str_lo"], ba["ZY-BERT vs Qwen3"]["str_lo"]), ("4.55", "8.59"))
        self.assertEqual(ba["ZY-BERT vs MacBERT"]["ord_source"], "audits/20261110_ba_reverification/results/pairwise_balanced_accuracy_bootstrap_seed42_corrected.csv")
        self.assertTrue(ba["ZY-BERT vs MacBERT"]["str_source"].startswith("results/pairwise_class_sensitive_stratified"))

        with (ROOT / "results" / "pairwise_class_sensitive_stratified_bootstrap_seed42.csv").open(encoding="utf-8") as handle:
            srows = {(r["pair"], r["metric"]): r for r in csv.DictReader(handle)}
        self.assertEqual(srows[("zybert_vs_internlm3", "balanced_accuracy")]["ordinary_ci_upper"], "0.0787")
        self.assertEqual(srows[("zybert_vs_macbert", "balanced_accuracy")]["diff_obs_unrounded_4dp"], "0.0670")
        self.assertEqual(srows[("internlm3_vs_macbert", "balanced_accuracy")]["diff_obs_unrounded_4dp"], "0.0093")
        self.assertEqual(srows[("zybert_vs_macbert", "balanced_accuracy")]["diff_obs_full_precision"], "0.0669567683389108")
        self.assertEqual(srows[("internlm3_vs_macbert", "balanced_accuracy")]["diff_obs_full_precision"], "0.0092578040986868")

    def test_redraw_source_contains_final_semantic_guards(self):
        source = (ROOT / "figures_py" / "redraw_new_reference_20261122.py").read_text(encoding="utf-8")
        for marker in (
            'dedup_sensitivity_seed42.csv',
            'fig6_bootstrap.csv',
            'diff_obs_unrounded_4dp',
            'diff_obs_full_precision',
            '(-int(classwise[j]["support"]), int(classwise[j]["label_id"]))',
            'Reference taxonomy (context)',
            'activation schematic',
            'Discordant: n10 vs n01',
            'Both 95% confidence intervals',
            'Empty model outputs',
            'Schematic matrix icons',
            '("Inquiry",orange)',
        ):
            self.assertIn(marker, source)
        for forbidden in (
            '(82.3,78.2,72.0,63.2)',
            '("Ordinary",blue,-1.46,3.31)',
            '("Macro-F1",3.21,3.11)',
            'float(sr["diff_obs"])*100',
            '("Tongue",orange)',
        ):
            self.assertNotIn(forbidden, source)

        # Verify precision separation in stratified CSV against frozen 42x42 confusion matrices
        with (ROOT / "figures_py" / "source_data" / "classwise_metrics.csv").open(encoding="utf-8-sig") as fh:
            cw_sup = [int(r["support"]) for r in csv.DictReader(fh)]
        mats = {}
        for m in ("zybert", "internlm3", "macbert", "qwen3"):
            with (ROOT / "results" / f"confusion_matrix_{m}.csv").open(encoding="utf-8-sig") as fh:
                rows = list(csv.reader(fh))
            mats[m] = [[int(x) for x in r[1:]] for r in rows[1:]]
        ba_exact = {m: sum(mats[m][i][i] / cw_sup[i] for i in range(42)) / 42.0 for m in mats}
        mf1_exact = {
            m: sum(
                2 * mats[m][i][i] / (cw_sup[i] + sum(mats[m][j][i] for j in range(42)))
                for i in range(42)
            ) / 42.0
            for m in mats
        }
        with (ROOT / "results" / "pairwise_class_sensitive_stratified_bootstrap_seed42.csv").open(encoding="utf-8-sig") as fh:
            strat_rows = list(csv.DictReader(fh))
        for row in strat_rows:
            ref = ba_exact if row["metric"] == "balanced_accuracy" else mf1_exact
            expected = ref[row["model_a"]] - ref[row["model_b"]]
            self.assertGreater(len(row["diff_obs_full_precision"].split(".")[1]), 10)
            self.assertAlmostEqual(float(row["diff_obs_full_precision"]), expected, places=12)
            self.assertEqual(f"{expected:.4f}", row["diff_obs_unrounded_4dp"])

    def test_figure7_scatter_no_legend_occlusion_and_figure8_validity_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["TCM_SD42_REPO"] = str(ROOT)
            env["TCM_SD42_OUT"] = tmp
            subprocess.run([sys.executable, str(ROOT / "figures_py" / "redraw_new_reference_20261122.py")], env=env, check=True)

            fig2_svg = (Path(tmp) / "SVG" / "Figure2.svg").read_text(encoding="utf-8")
            self.assertIn(">Inquiry<", fig2_svg)
            self.assertNotIn(">Tongue<", fig2_svg)

            fig7_svg = (Path(tmp) / "SVG" / "Figure7.svg").read_text(encoding="utf-8")
            # Legend box in Figure 7B F1 vs. class support is at x=46..412, y=463..483
            lx, ly, lw, lh = 46.0, 463.0, 366.0, 20.0
            x0, x1 = 92.0, 399.0
            pts = [
                (float(cx), float(cy), float(r))
                for cx, cy, r in re.findall(r'<circle cx="([^"]+)" cy="([^"]+)" r="([^"]+)" fill="#(?:1769c2|e35b22|3c7c4f|7c4cad)"', fig7_svg)
                if abs(float(r) - 2.7) < 1e-6 and 80.0 <= float(cx) <= 415.0 and 450.0 <= float(cy) <= 630.0
            ]
            self.assertEqual(len(pts), 168)
            for cx, cy, r in pts:
                overlap_x = (cx + r) >= lx and (cx - r) <= (lx + lw)
                overlap_y = (cy + r) >= ly and (cy - r) <= (ly + lh)
                self.assertFalse(overlap_x and overlap_y, f"Scatter point {(cx, cy, r)} overlaps legend box")
                self.assertGreater(cx - r, x0, f"Scatter point {(cx, cy, r)} crosses left spine x={x0}")
                self.assertLess(cx + r, x1, f"Scatter point {(cx, cy, r)} crosses right boundary x={x1}")

            fig8_svg = (Path(tmp) / "SVG" / "Figure8.svg").read_text(encoding="utf-8")
            parser_boxes = re.findall(r'<rect x="([^"]+)" y="([^"]+)" width="([^"]+)" height="([^"]+)"[^>]*/>\s*<text[^>]*>Parser v18</text>', fig8_svg)
            counts_4216 = re.findall(r'<text x="([^"]+)" y="([^"]+)"[^>]*>4,216 / 4,218</text>', fig8_svg)
            self.assertEqual(len(parser_boxes), 2)
            self.assertEqual(len(counts_4216), 2)
            for (_, py, _, ph), (_, cy) in zip(parser_boxes, counts_4216):
                self.assertLess(float(cy), float(py), "4,216 / 4,218 label must sit strictly above Parser v18 box")

    def test_fig8_errors_chinese_labels_complete(self):
        import json
        labels = json.loads((SOURCE / "syndrome_label_list.json").read_text(encoding="utf-8"))
        id_to_zh = {f"C{i+1:02d}": lab for i, lab in enumerate(labels)}
        with (SOURCE / "fig8_errors.csv").open(encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 10)
        for r in rows:
            self.assertTrue(r["true_zh"].strip())
            self.assertTrue(r["pred_zh"].strip())
            self.assertEqual(r["true_zh"], id_to_zh[r["true_id"]])
            self.assertEqual(r["pred_zh"], id_to_zh[r["pred_id"]])


if __name__ == "__main__":
    unittest.main()
