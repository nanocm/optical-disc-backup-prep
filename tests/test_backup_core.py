from __future__ import annotations

import shutil
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backup_core import (  # noqa: E402
    BackupError,
    BackupPlan,
    compose_disc_id,
    create_batch,
    generate_manifest,
    load_existing_disc,
    save_about,
    verify_batch,
    _is_optical_path,
)


TEST_TMP = Path(__file__).resolve().parent / ".tmp"


class BackupCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        TEST_TMP.mkdir(exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="case-", dir=TEST_TMP))
        self.assertTrue(self.root.resolve().is_relative_to(TEST_TMP.resolve()))
        self.output = self.root / "staging"
        self.output.mkdir()

    def tearDown(self) -> None:
        self.assertTrue(self.root.resolve().is_relative_to(TEST_TMP.resolve()))
        shutil.rmtree(self.root)

    def plan(self, batch_number: int = 1, media: str = "BD-R 25 GB",
             omit_about: bool = False) -> BackupPlan:
        return BackupPlan(
            output_root=self.output, disc_id="DISC-0001", media=media,
            mid="VERBAT-IMe-000", batch_number=batch_number,
            batch_date="2026-10-06", title="Photos", omit_about=omit_about,
        )

    def test_create_empty_then_save_about_then_hash_and_verify(self) -> None:
        batch = create_batch(self.plan())
        self.assertEqual((batch / "ABOUT.txt").stat().st_size, 0)
        self.assertEqual((batch / "SHA256SUMS.txt").stat().st_size, 0)
        self.assertTrue((batch / "DATA").is_dir())
        with self.assertRaises(BackupError):
            verify_batch(batch)

        (batch / "DATA" / "Photos" / "2024").mkdir(parents=True)
        (batch / "DATA" / "Photos" / "2024" / "中文 名称.txt").write_bytes(b"hello")
        (batch / "DATA" / ".hidden").write_bytes(b"hidden")
        save_about(batch, "来源：家庭照片\n版本：1")
        manifest = generate_manifest(batch)
        self.assertEqual(len(manifest.read_text(encoding="utf-8").splitlines()), 3)
        self.assertTrue(verify_batch(batch).passed)
        info = (self.output / "DISC-0001" / "DISC_INFO.txt").read_text(encoding="utf-8")
        self.assertIn("DiscID: DISC-0001", info)
        self.assertIn("Media: BD-R 25 GB", info)
        self.assertIn("DirectoryConvention: Bnn_YYYY-MM-DD_Title", info)
        self.assertNotIn("DriveObserved:", info)
        self.assertNotIn("CapacityBytesReportedByWindows:", info)

    def test_about_update_invalidates_old_manifest(self) -> None:
        batch = create_batch(self.plan())
        (batch / "DATA" / "file.txt").write_bytes(b"content")
        save_about(batch, "第一版")
        generate_manifest(batch)
        with self.assertRaises(BackupError):
            save_about(batch, "第二版")
        save_about(batch, "第二版", invalidate_manifest=True)
        self.assertEqual((batch / "SHA256SUMS.txt").stat().st_size, 0)
        with self.assertRaises(BackupError):
            verify_batch(batch)
        generate_manifest(batch)
        self.assertTrue(verify_batch(batch).passed)

    def test_data_changes_are_detected_and_refresh_requires_confirmation(self) -> None:
        batch = create_batch(self.plan())
        file = batch / "DATA" / "file.txt"
        file.write_bytes(b"before")
        save_about(batch, "来源：测试")
        generate_manifest(batch)
        file.write_bytes(b"after")
        (batch / "DATA" / "new.txt").write_bytes(b"extra")
        result = verify_batch(batch)
        self.assertFalse(result.passed)
        self.assertTrue(any("哈希不符：DATA/file.txt" in problem for problem in result.problems))
        self.assertTrue(any("清单未列" in problem for problem in result.problems))
        with self.assertRaises(BackupError):
            generate_manifest(batch)
        generate_manifest(batch, replace=True)
        self.assertTrue(verify_batch(batch).passed)

    def test_second_batch_keeps_existing_disc_info(self) -> None:
        create_batch(self.plan())
        info = self.output / "DISC-0001" / "DISC_INFO.txt"
        original = info.read_bytes()
        batch2 = create_batch(self.plan(batch_number=2))
        self.assertTrue(batch2.name.startswith("B02_"))
        self.assertEqual(info.read_bytes(), original)
        with self.assertRaises(BackupError):
            create_batch(self.plan(batch_number=3, media="DVD-R 4.7 GB"))
        with self.assertRaises(BackupError):
            create_batch(self.plan())

    def test_empty_about_or_data_cannot_be_hashed(self) -> None:
        batch = create_batch(self.plan())
        with self.assertRaises(BackupError):
            generate_manifest(batch)
        save_about(batch, "来源：测试")
        with self.assertRaises(BackupError):
            generate_manifest(batch)

    def test_explicitly_omit_about_and_hash_nested_data(self) -> None:
        batch = create_batch(self.plan(omit_about=True))
        self.assertFalse((batch / "ABOUT.txt").exists())
        nested = batch / "DATA" / "Photos" / "2024"
        nested.mkdir(parents=True)
        (nested / "a.jpg").write_bytes(b"photo")
        (batch / "DATA" / "empty-folder").mkdir()
        manifest = generate_manifest(batch, omit_about=True)
        lines = manifest.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].endswith("  DATA/Photos/2024/a.jpg"))
        self.assertTrue(verify_batch(batch).passed)

    def test_opt_out_removes_only_empty_about(self) -> None:
        batch = create_batch(self.plan())
        (batch / "DATA" / "a.txt").write_bytes(b"data")
        generate_manifest(batch, omit_about=True)
        self.assertFalse((batch / "ABOUT.txt").exists())
        self.assertTrue(verify_batch(batch).passed)

    def test_opt_out_rejects_nonempty_about(self) -> None:
        batch = create_batch(self.plan())
        (batch / "DATA" / "a.txt").write_bytes(b"data")
        save_about(batch, "保留这份说明")
        with self.assertRaises(BackupError):
            generate_manifest(batch, omit_about=True)
        self.assertEqual((batch / "ABOUT.txt").read_text(encoding="utf-8"), "保留这份说明\n")
        self.assertEqual((batch / "SHA256SUMS.txt").stat().st_size, 0)

    def test_compose_disc_id(self) -> None:
        self.assertEqual(compose_disc_id("arc", "bdr25", "001"), "ARC_BDR25_001")
        for parts in (("ARC", "BDR25", ""), ("ARC", "BD-R25", "001"),
                      ("ARC", "BDR25", "A01")):
            with self.subTest(parts=parts), self.assertRaises(BackupError):
                compose_disc_id(*parts)

    def test_existing_disc_batch(self) -> None:
        create_batch(self.plan())
        existing = load_existing_disc(self.output / "DISC-0001")
        self.assertEqual(existing.disc_id, "DISC-0001")
        self.assertEqual(existing.media, "BD-R 25 GB")
        self.assertEqual(existing.mid, "VERBAT-IMe-000")
        self.assertEqual(existing.next_batch_number, 2)
        self.assertEqual(existing.output_root, self.output)
        create_batch(self.plan(batch_number=2))
        self.assertEqual(load_existing_disc(self.output / "DISC-0001").next_batch_number, 3)

    def test_existing_disc_requires_valid_info(self) -> None:
        wrong = self.output / "DISC-0008"
        wrong.mkdir()
        with self.assertRaises(BackupError):
            load_existing_disc(wrong)
        (wrong / "DISC_INFO.txt").write_text("DiscID: DISC-0009\nMedia: BD-R 25 GB\n", encoding="utf-8")
        with self.assertRaises(BackupError):
            load_existing_disc(wrong)

    @unittest.skipUnless(os.name == "nt" and _is_optical_path(Path("G:/")), "G: is not an optical drive")
    def test_never_creates_a_batch_on_optical_drive(self) -> None:
        plan = BackupPlan(
            output_root=Path("G:/"), disc_id="DISC-0001", media="BD-R 25 GB",
            mid="", batch_number=1, batch_date="2026-10-06", title="Photos",
        )
        with self.assertRaises(BackupError):
            create_batch(plan)


if __name__ == "__main__":
    unittest.main()
