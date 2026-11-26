"""Regression checks for class metrics and frozen label extraction."""
import importlib.util
from pathlib import Path
import unittest

CODE = Path(__file__).resolve().parents[1] / "code"


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, CODE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


evaluate = load_module("evaluate")


class PerClassMetricsTests(unittest.TestCase):
    def test_empty_predictions_remain_false_negatives(self):
        metrics = evaluate.compute_metrics(
            ["a", "a", "b", "b"], ["a", "empty", "b", "a"], ["a", "b", "c"]
        )
        self.assertEqual(
            metrics["per_class"],
            {
                "a": {"precision": 0.5, "recall": 0.5, "f1": 0.5, "support": 2},
                "b": {"precision": 1.0, "recall": 0.5, "f1": 0.6667, "support": 2},
                "c": {"precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 0},
            },
        )
        self.assertEqual(metrics["syn_acc@1"], 0.5)
        self.assertEqual(metrics["macro_f1"], 0.3889)
        self.assertEqual(metrics["balanced_accuracy"], 0.5)
        self.assertEqual(
            evaluate.confusion_matrix_df(
                ["a", "a", "b", "b"], ["a", "empty", "b", "a"], ["a", "b", "c"]
            ).tolist(),
            [[1, 0, 0], [1, 1, 0], [0, 0, 0]],
        )

    def test_all_invalid_predictions_preserve_gold_support(self):
        metrics = evaluate.compute_metrics(
            ["a", "b"], ["empty", "out-of-vocabulary"], ["a", "b"]
        )
        for label in ("a", "b"):
            self.assertEqual(
                metrics["per_class"][label],
                {"precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 1},
            )


class OutputTemplateTests(unittest.TestCase):
    def test_parser_and_strict_template_measure_different_properties(self):
        import sys
        from tempfile import TemporaryDirectory
        import json
        sys.path.insert(0, str(CODE))
        try:
            strict = load_module("audit_output_format")
        finally:
            sys.path.remove(str(CODE))
        label = "心血瘀阻"
        outputs = [
            f"证型：{label}\n辨证依据：示例依据",
            f"辨证依据：文本含有{label}",
            f"证型：{label}证\n辨证依据：示例依据",
            "",
        ]
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw_outputs.jsonl"
            path.write_text(
                "\n".join(json.dumps({"raw_output": output}) for output in outputs),
                encoding="utf-8",
            )
            self.assertEqual(
                strict.audit_outputs(path),
                {"n": 4, "parsed_count": 3, "strict_count": 1,
                 "valid_label_extraction_rate": 0.75, "strict_template_compliance_rate": 0.25},
            )
