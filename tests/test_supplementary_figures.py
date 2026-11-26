#!/usr/bin/env python3
"""Public aggregate and rendering tests for Supplementary Figures S0-S4."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "figures_py"))
from make_supp_figures import generate_all, validate_inputs


class SupplementaryFigureTests(unittest.TestCase):
    def test_public_matrices_and_top10_rows_reconcile(self):
        matrices, _, summary = validate_inputs()
        self.assertEqual(
            [summary[k]["top10"] for k in ("zybert", "internlm3", "macbert", "qwen3")],
            [324, 409, 640, 667],
        )
        self.assertEqual(
            [summary[k]["valid_n"] for k in ("zybert", "internlm3", "macbert", "qwen3")],
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
                "FigureS1.png", "FigureS1.svg",
                "FigureS2.png", "FigureS2.svg",
                "FigureS3.png", "FigureS3.svg",
                "FigureS4.png", "FigureS4.svg",
            ]
            for name in expected:
                path = output / name
                self.assertTrue(path.is_file(), name)
                self.assertGreater(path.stat().st_size, 100, name)


if __name__ == "__main__":
    unittest.main()
