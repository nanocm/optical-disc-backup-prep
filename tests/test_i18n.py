from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from i18n import EN, localize_core, tr  # noqa: E402


class TranslationTests(unittest.TestCase):
    def test_every_static_gui_message_has_an_english_entry(self) -> None:
        tree = ast.parse((ROOT / "backup_gui.py").read_text(encoding="utf-8"))
        keys = {
            node.args[0].value
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "t"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        }
        self.assertFalse(keys - EN.keys(), f"Missing English text: {keys - EN.keys()}")

    def test_core_errors_and_paths_translate_without_changing_filenames(self) -> None:
        self.assertEqual(tr("盘号", "en"), "Disc ID")
        self.assertEqual(localize_core("哈希不符：DATA/照片.jpg", "en"),
                         "Hash mismatch: DATA/照片.jpg")
        self.assertIn("line 3", localize_core("SHA256SUMS.txt 第 3 行格式或路径无效。", "en"))
        self.assertEqual(localize_core("哈希不符：DATA/照片.jpg", "zh"),
                         "哈希不符：DATA/照片.jpg")


if __name__ == "__main__":
    unittest.main()
