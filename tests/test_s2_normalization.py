import pathlib
import re
import types
import unicodedata
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "code" / "recompute_pairwise_stats.py"


def load_norm_text():
    source = SCRIPT.read_text(encoding="utf-8")
    start = source.index("def norm_text(")
    end = source.index("\ndef sha(", start)
    module = types.ModuleType("norm_text_only")
    module.__dict__.update({"unicodedata": unicodedata, "re": re})
    exec(compile(source[start:end], "norm_text_only", "exec"), module.__dict__)
    return module.norm_text


norm_text = load_norm_text()


class S2NormalizationTests(unittest.TestCase):
    def test_delete_is_default(self):
        self.assertEqual(norm_text("发热3天"), "发热天")
        self.assertEqual(norm_text("abc123def"), "abcdef")
        self.assertEqual(norm_text("无数字"), "无数字")

    def test_sentinel_is_explicit_comparison_mode(self):
        self.assertEqual(norm_text("发热3天", "sentinel"), "发热#天")
        self.assertEqual(norm_text("患者5岁", "sentinel"), "患者#岁")

    def test_modes_differ_when_only_one_text_has_digits(self):
        self.assertNotEqual(norm_text("发热3天"), norm_text("发热3天", "sentinel"))
        self.assertEqual(norm_text("无数字"), norm_text("无数字", "sentinel"))

    def test_unknown_mode_fails_closed(self):
        with self.assertRaises(ValueError):
            norm_text("发热3天", "unknown")


if __name__ == "__main__":
    unittest.main()
