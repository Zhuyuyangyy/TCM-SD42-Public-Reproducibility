import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "code" / "recompute_pairwise_stats.py"

spec = importlib.util.spec_from_file_location("recompute_pairwise_stats", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class S2NormalizationTests(unittest.TestCase):
    def test_delete_is_default(self):
        self.assertEqual(module.norm_text("发热3天"), "发热天")
        self.assertEqual(module.norm_text("abc123def"), "abcdef")
        self.assertEqual(module.norm_text("无数字"), "无数字")

    def test_sentinel_is_explicit_comparison_mode(self):
        self.assertEqual(module.norm_text("发热3天", "sentinel"), "发热#天")
        self.assertEqual(module.norm_text("患者5岁", "sentinel"), "患者#岁")

    def test_modes_differ_when_only_one_text_has_digits(self):
        self.assertNotEqual(module.norm_text("发热3天"), module.norm_text("发热3天", "sentinel"))
        self.assertEqual(module.norm_text("无数字"), module.norm_text("无数字", "sentinel"))

    def test_unknown_mode_fails_closed(self):
        with self.assertRaises(ValueError):
            module.norm_text("发热3天", "unknown")


if __name__ == "__main__":
    unittest.main()
