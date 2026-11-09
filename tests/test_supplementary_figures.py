#!/usr/bin/env python3
"""Public aggregate and rendering tests for Supplementary Figures S0-S4."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "figures_py"))
from reproduce_supplementary import generate_all, load_inputs


class SupplementaryFigureTests(unittest.TestCase):
    def test_public_matrices_and_top10_rows_reconcile(self):
        labels, matrices, error_rows, summaries = load_inputs()
        self.assertEqual(len(labels), 42)
        self.assertEqual(len(error_rows), 10)
        self.assertEqual(
            [summaries[name]["top10"] for name in ("ZY-BERT", "InternLM3-8B", "MacBERT", "Qwen3-8B")],
            [324, 409, 640, 667],
        )
        self.assertEqual(
            [summaries[name]["valid_n"] for name in ("ZY-BERT", "InternLM3-8B", "MacBERT", "Qwen3-8B")],
            [4218, 4216, 4218, 4216],
        )
        for matrix in matrices.values():
            self.assertEqual(matrix.shape, (42, 42))

    def test_all_five_figures_render_to_png_and_svg(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            generate_all(output, dpi=72)
            expected = [
                "FigureS0.png", "FigureS0.svg",
                "FigureS1_zybert.png", "FigureS1_zybert.svg",
                "FigureS2_internlm3.png", "FigureS2_internlm3.svg",
                "FigureS3_macbert.png", "FigureS3_macbert.svg",
                "FigureS4_qwen3.png", "FigureS4_qwen3.svg",
            ]
            for name in expected:
                path = output / name
                self.assertTrue(path.is_file(), name)
                self.assertGreater(path.stat().st_size, 100, name)


if __name__ == "__main__":
    unittest.main()
