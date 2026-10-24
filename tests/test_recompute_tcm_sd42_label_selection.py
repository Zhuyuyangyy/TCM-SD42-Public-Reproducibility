import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "code" / "recompute_tcm_sd42_label_selection.py"

class LabelSelectionRecomputeTests(unittest.TestCase):
    def write_json(self, path, labels):
        rows = [{"syndrome": label, "id": f"{path.stem}_{i}"} for i, label in enumerate(labels)]
        path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")

    def test_cap_before_vs_after_canonicalization_is_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            train = root / "train.json"
            dev = root / "dev.json"
            test = root / "test.json"
            labels = root / "labels.txt"
            frozen = root / "frozen_support.csv"
            out = root / "out"

            train_labels = (
                ["正虚瘀结证"] * 1000
                + ["正虚瘀结"] * 227
                + ["气虚血瘀"] * 100
            )
            dev_labels = ["正虚瘀结证"] * 10 + ["正虚瘀结"] * 10 + ["气虚血瘀"] * 10
            test_labels = ["正虚瘀结证"] * 10 + ["正虚瘀结"] * 10 + ["气虚血瘀"] * 10
            self.write_json(train, train_labels)
            self.write_json(dev, dev_labels)
            self.write_json(test, test_labels)
            labels.write_text("正虚瘀结\n气虚血瘀\n", encoding="utf-8")
            with frozen.open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["syndrome", "train_count", "dev_count", "test_count"])
                w.writeheader()
                w.writerows([
                    {"syndrome": "正虚瘀结", "train_count": 1000, "dev_count": 20, "test_count": 20},
                    {"syndrome": "气虚血瘀", "train_count": 100, "dev_count": 10, "test_count": 10},
                ])

            cmd = [
                sys.executable, str(SCRIPT),
                "--train", str(train), "--dev", str(dev), "--test", str(test),
                "--label-field", "syndrome", "--frozen-labels", str(labels),
                "--frozen-support-csv", str(frozen), "--out-dir", str(out),
                "--expected-train", str(len(train_labels)), "--expected-dev", str(len(dev_labels)),
                "--expected-test", str(len(test_labels)),
                "--reported-final-train", "1100", "--reported-final-dev", "30", "--reported-final-test", "30",
            ]
            run = subprocess.run(cmd, check=True, capture_output=True, text=True)
            result = json.loads((out / "label_selection_recompute.json").read_text(encoding="utf-8"))
            self.assertTrue(result["frozen_label_comparison"]["exact_set_match"])
            self.assertEqual(result["label_counts"]["eligible_raw_strings"], 3)
            self.assertEqual(result["label_counts"]["selected_canonical_labels"], 2)
            self.assertEqual(result["cap_order_comparison"]["cap_each_raw_label_then_merge"]["train"], 1327)
            self.assertEqual(result["cap_order_comparison"]["merge_eligible_raw_labels_then_cap_each_canonical_label"]["train"], 1100)
            self.assertEqual(result["cap_order_comparison"]["train_difference_between_cap_orders"], 227)
            self.assertTrue(result["cap_order_comparison"]["canonical_cap_train_equals_reported_frozen_train"])
            self.assertTrue(result["frozen_support_csv_comparison"]["canonical_train_support_match"])
            self.assertIn('"top_k_binding": false', run.stdout)

    def test_trailing_suffix_canonicalization_is_not_applied_twice(self):
        # A label with no trailing 证 is preserved; exactly one trailing character is removed.
        cmd = [sys.executable, "-c",
               "import runpy; m=runpy.run_path(r'" + str(SCRIPT) + "'); "
               "assert m['canonicalize']('正虚瘀结证') == '正虚瘀结'; "
               "assert m['canonicalize']('正虚瘀结') == '正虚瘀结'"]
        subprocess.run(cmd, check=True, capture_output=True, text=True)

if __name__ == "__main__":
    unittest.main()
