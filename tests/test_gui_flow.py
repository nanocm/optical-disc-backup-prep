from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backup_core import verify_batch  # noqa: E402
from backup_gui import BackupGUI, read_optical_drives  # noqa: E402


TEST_TMP = Path(__file__).resolve().parent / ".tmp"


class GUIFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        TEST_TMP.mkdir(exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="gui-", dir=TEST_TMP))
        self.assertTrue(self.root.resolve().is_relative_to(TEST_TMP.resolve()))

    def tearDown(self) -> None:
        self.assertTrue(self.root.resolve().is_relative_to(TEST_TMP.resolve()))
        shutil.rmtree(self.root)

    def test_media_query_requires_explicit_request(self) -> None:
        response = subprocess.CompletedProcess([], 0, '{"Drives":[],"Error":null}', "")
        with patch("backup_gui.subprocess.run", return_value=response) as run:
            read_optical_drives()
            self.assertNotIn("-IncludeMedia", run.call_args.args[0])
            read_optical_drives(include_media=True, drive_letter="G:")
            self.assertEqual(run.call_args.args[0][-3:], ["-IncludeMedia", "-DriveLetter", "G:"])

    def test_drive_only_inventory_keeps_media_unread(self) -> None:
        app = BackupGUI()
        app.after_cancel(app.startup_drive_after)
        try:
            drive = {"DriveLetter": "G:", "Vendor": "ASUS", "Product": "BW-16D1HT",
                     "Revision": "3.10", "MediaQueried": False, "MediaTypeCode": None}
            app._apply_discs([drive], include_media=False)
            self.assertIn("尚未读取", app.disc_summary.get())
            self.assertEqual(app.media_var.get(), "")
            app._apply_discs([{**drive, "MediaQueried": True, "MediaTypeCode": 19}], include_media=True)
            self.assertIn("BD-R", app.disc_summary.get())
            self.assertEqual(app.media_var.get(), "BD-R")
        finally:
            for event_id in app.tk.call("after", "info"):
                app.after_cancel(event_id)
            app.destroy()

    def test_create_save_about_generate_manifest(self) -> None:
        with patch("backup_gui.messagebox.showinfo"), patch("backup_gui.messagebox.showerror") as errors:
            app = BackupGUI()
            app.after_cancel(app.startup_drive_after)
            try:
                app.output_var.set(str(self.root))
                app.middle_var.set("BDR25")
                app.suffix_var.set("001")
                self.assertEqual(app.disc_id_var.get(), "ARC_BDR25_001")
                app.media_var.set("BD-R 25 GB")
                app.title_var.set("Photos")
                app.about_text.insert("1.0", "来源：我整理的照片")
                app._create_batch()
                batch = Path(app.batch_path_var.get())
                self.assertTrue(batch.is_dir())
                self.assertEqual((batch / "ABOUT.txt").stat().st_size, 0)
                self.assertIn("我整理的照片", app.about_text.get("1.0", "end"))
                (batch / "DATA" / "hello.txt").write_bytes(b"hello")
                app._save_about()
                self.assertIn("我整理的照片", (batch / "ABOUT.txt").read_text(encoding="utf-8"))
                app._generate_manifest()
                deadline = time.time() + 10
                while app.busy and time.time() < deadline:
                    app.update()
                    time.sleep(.02)
                app.update()
                self.assertFalse(app.busy)
                self.assertTrue(verify_batch(batch).passed)
                errors.assert_not_called()
            finally:
                for event_id in app.tk.call("after", "info"):
                    app.after_cancel(event_id)
                app.destroy()

    def test_compose_number_then_reuse_for_next_batch(self) -> None:
        with patch("backup_gui.messagebox.showinfo"), patch("backup_gui.messagebox.showerror") as errors:
            app = BackupGUI()
            app.after_cancel(app.startup_drive_after)
            try:
                app.output_var.set(str(self.root))
                app.middle_var.set("BDR25")
                app.suffix_var.set("001")
                self.assertEqual(app.disc_id_var.get(), "ARC_BDR25_001")
                app.media_var.set("BD-R 25 GB")
                app.title_var.set("Docs")
                app._create_batch()
                disc_dir = self.root / "ARC_BDR25_001"
                with patch("backup_gui.filedialog.askdirectory", return_value=str(disc_dir)):
                    app._use_existing_disc()
                self.assertEqual(app.disc_id_var.get(), "ARC_BDR25_001")
                self.assertEqual(app.prefix_var.get(), "ARC")
                self.assertEqual(app.middle_var.get(), "BDR25")
                self.assertEqual(app.suffix_var.get(), "001")
                self.assertEqual(app.media_var.get(), "BD-R 25 GB")
                self.assertEqual(app.batch_no_var.get(), "02")
                self.assertEqual(app.batch_path_var.get(), "")
                errors.assert_not_called()
            finally:
                for event_id in app.tk.call("after", "info"):
                    app.after_cancel(event_id)
                app.destroy()

    def test_checkbox_omits_about_from_batch_and_manifest(self) -> None:
        with patch("backup_gui.messagebox.showinfo"), patch("backup_gui.messagebox.showerror") as errors:
            app = BackupGUI()
            app.after_cancel(app.startup_drive_after)
            try:
                app.output_var.set(str(self.root))
                app.middle_var.set("BDR25")
                app.suffix_var.set("002")
                app.media_var.set("BD-R 25 GB")
                app.title_var.set("Photos")
                app.omit_about_var.set(True)
                app._on_about_option_changed()
                app._create_batch()
                batch = Path(app.batch_path_var.get())
                self.assertFalse((batch / "ABOUT.txt").exists())
                nested = batch / "DATA" / "2024"
                nested.mkdir()
                (nested / "a.jpg").write_bytes(b"photo")
                app._generate_manifest()
                deadline = time.time() + 10
                while app.busy and time.time() < deadline:
                    app.update()
                    time.sleep(.02)
                app.update()
                self.assertFalse(app.busy)
                self.assertTrue(verify_batch(batch).passed)
                self.assertNotIn("ABOUT.txt", (batch / "SHA256SUMS.txt").read_text(encoding="utf-8"))
                errors.assert_not_called()
            finally:
                for event_id in app.tk.call("after", "info"):
                    app.after_cancel(event_id)
                app.destroy()


if __name__ == "__main__":
    unittest.main()
