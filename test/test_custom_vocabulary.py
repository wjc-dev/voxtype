import tempfile
import unittest
from pathlib import Path

from src.custom_vocabulary import load_custom_vocabulary


class CustomVocabularyTests(unittest.TestCase):
    def test_loads_deduplicates_and_ignores_comments(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "custom_vocabulary.txt"
            path.write_text(
                "项目代号\nLightGBM\nlightgbm\n# 这是注释\n\ntrade-off\n",
                encoding="utf-8",
            )

            self.assertEqual(
                load_custom_vocabulary(path),
                ["项目代号", "LightGBM", "trade-off"],
            )

    def test_limits_terms_and_rejects_unreasonable_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "custom_vocabulary.txt"
            path.write_text(
                "有效人名\n" + "x" * 65 + "\none two three four five six seven eight\n另一个\n",
                encoding="utf-8",
            )

            self.assertEqual(load_custom_vocabulary(path, limit=1), ["有效人名"])


if __name__ == "__main__":
    unittest.main()
