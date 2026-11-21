#!/usr/bin/env python3
"""Filesystem tests for the decoded-source patch engine."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from apk_patch import PatchManager, safe_rel  # noqa: E402


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class TestPatchManager(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.src = self.root / "decoded" / "app"
        self.manager = PatchManager(self.root / "patches", workspace=self.root)
        write(self.src / "AndroidManifest.xml", "<manifest/>")
        write(self.src / "smali" / "com" / "example" / "Main.smali", ".class public Main")
        write(self.src / "res" / "values" / "strings.xml", "<resources/>")

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_snapshot_copies_content(self):
        rec = self.manager.create(self.src, "baseline")
        self.assertEqual(rec["kind"], "snapshot")
        self.assertEqual(rec["file_count"], 3)
        content = self.manager._has_content(rec)
        self.assertTrue((content / "AndroidManifest.xml").is_file())
        self.assertTrue((content / "smali/com/example/Main.smali").is_file())
        self.assertTrue((self.root / "patches" / f"patch_{rec['id']}.json").is_file())

    def test_diff_detects_modified_added_deleted(self):
        rec = self.manager.create(self.src)
        write(self.src / "AndroidManifest.xml", "<manifest changed/>")
        write(self.src / "smali" / "com" / "example" / "New.smali", ".class public New")
        (self.src / "res" / "values" / "strings.xml").unlink()
        changes = self.manager.diff(self.src, rec)
        self.assertEqual(changes["modified"], ["AndroidManifest.xml"])
        self.assertEqual(changes["added"], ["smali/com/example/New.smali"])
        self.assertEqual(changes["deleted"], ["res/values/strings.xml"])

    def test_rollback_restores_and_backs_up(self):
        rec = self.manager.create(self.src)
        write(self.src / "AndroidManifest.xml", "<manifest EDITOR/>)")
        result = self.manager.rollback(self.src, rec)
        self.assertIn("AndroidManifest.xml", result["restored"])
        self.assertEqual(
            (self.src / "AndroidManifest.xml").read_text(encoding="utf-8"), "<manifest/>"
        )
        self.assertEqual(len(result["backed_up"]), 1)
        backed = Path(result["backed_up"][0])
        self.assertTrue(backed.is_file())
        self.assertIn("before_rollback", str(backed))
        self.assertEqual(backed.read_text(encoding="utf-8"), "<manifest EDITOR/>)")

    def test_rollback_moves_new_files_to_backup_never_deletes(self):
        rec = self.manager.create(self.src)
        extra = write(self.src / "res" / "values" / "extra.xml", "<extra/>")
        result = self.manager.rollback(self.src, rec)
        self.assertFalse(extra.exists())
        moved = Path(result["removed_from_source"][0])
        self.assertTrue(moved.is_file())
        self.assertEqual(moved.read_text(encoding="utf-8"), "<extra/>")

    def test_dry_run_writes_nothing(self):
        rec = self.manager.create(self.src)
        write(self.src / "AndroidManifest.xml", "<manifest EDITOR/>)")
        result = self.manager.rollback(self.src, rec, dry_run=True)
        self.assertTrue(result["dry_run"])
        self.assertEqual(
            (self.src / "AndroidManifest.xml").read_text(encoding="utf-8"), "<manifest EDITOR/>)"
        )
        self.assertFalse(any((self.root / "backup").glob("**/*")))

    def test_export_and_apply_roundtrip(self):
        rec = self.manager.create(self.src)
        write(self.src / "AndroidManifest.xml", "<manifest EDITED/>")

        target = self.root / "decoded" / "other"
        write(target / "AndroidManifest.xml", "<manifest ORIGINAL/>")
        write(target / "smali" / "com" / "example" / "Main.smali", ".class public Main")

        bundle = self.manager.export(self.src, rec, "mybundle")
        self.assertEqual(bundle["kind"], "bundle")
        self.assertEqual(bundle["file_count"], 1)

        result = self.manager.apply(target, bundle)
        self.assertEqual(result["applied"], ["AndroidManifest.xml"])
        self.assertEqual(
            (target / "AndroidManifest.xml").read_text(encoding="utf-8"), "<manifest EDITED/>"
        )
        self.assertTrue(any((self.root / "backup").glob("before_apply_*/*")))

    def test_empty_bundle_can_be_applied_as_noop(self):
        rec = self.manager.create(self.src)
        empty = self.manager.export(self.src, rec, "empty_bundle")
        self.assertEqual(empty["file_count"], 0)
        result = self.manager.apply(self.src, empty)
        self.assertEqual(result["applied"], [])

    def test_legacy_hash_record_cannot_be_restored(self):
        legacy = self.root / "patches" / "patch_legacy.json"
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_text(json.dumps({"source": str(self.src), "files": {}}), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.manager.load(legacy)

    def test_list_and_latest_for(self):
        first = self.manager.create(self.src, "first")
        second = self.manager.create(self.src, "second")
        records = self.manager.list_records()
        self.assertEqual(len(records), 2)
        self.assertEqual(self.manager.latest_for(self.src)["id"], second["id"])
        self.assertNotEqual(first["id"], second["id"])

    def test_path_traversal_rejected(self):
        for bad in ("../evil", "/etc/passwd", "a\\b", ""):
            with self.assertRaises(ValueError):
                safe_rel(bad)

    def test_apply_dry_run_does_not_write(self):
        rec = self.manager.create(self.src)
        write(self.src / "AndroidManifest.xml", "<manifest EDITED/>")
        bundle = self.manager.export(self.src, rec, "drybundle")
        write(self.src / "AndroidManifest.xml", "<manifest CURRENT/>")
        result = self.manager.apply(self.src, bundle, dry_run=True)
        self.assertTrue(result["dry_run"])
        self.assertEqual(
            (self.src / "AndroidManifest.xml").read_text(encoding="utf-8"), "<manifest CURRENT/>"
        )


if __name__ == "__main__":
    unittest.main()
