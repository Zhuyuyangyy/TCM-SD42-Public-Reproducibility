#!/usr/bin/env python3
"""Regression tests for sklearn-compatible balanced accuracy in the fast path."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
from sklearn.metrics import balanced_accuracy_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from pairwise_class_sensitive_bootstrap import fast_metrics


class BalancedAccuracyFastPathTests(unittest.TestCase):
    def test_prediction_only_class_is_not_in_balanced_accuracy_denominator(self):
        gold = np.array([0, 0, 1, 1], dtype=np.int64)
        pred = np.array([0, 0, 0, 2], dtype=np.int64)
        _, _, actual = fast_metrics(gold, pred)
        expected = balanced_accuracy_score(gold, pred)
        self.assertAlmostEqual(actual, expected, places=12)
        self.assertAlmostEqual(actual, 0.5, places=12)

    def test_out_of_label_empty_prediction_is_not_a_gold_class(self):
        gold = np.array([0, 0, 1, 1], dtype=np.int64)
        pred = np.array([0, 42, 1, 42], dtype=np.int64)
        _, _, actual = fast_metrics(gold, pred)
        expected = balanced_accuracy_score(gold, pred)
        self.assertAlmostEqual(actual, expected, places=12)


if __name__ == "__main__":
    unittest.main()
