#!/usr/bin/env python3
"""Tests for the audit result cache."""
import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import apk_cache as cache_mod  # noqa: E402
from apk_audit import APKAuditor  # noqa: E402
from apk_cache import AuditCache, CACHE_VERSION  # noqa: E402

SHA = "a" * 64


def fake_report(mode="normal", sha=SHA):
    return {
        "audit_metadata": {"sha256": sha, "mode": mode, "timestamp": "2026-01-01T00:00:00Z"},
        "basic_info": {"package_name": "org.example"},
    }


class TestAuditCache(unittest.TestCase):
    def test_key_is_stable_and_mode_specific(self):
        c = AuditCache("/tmp/anything")
        self.assertEqual(c.key(SHA, "fast"), c.key(SHA, "fast"))
        self.assertNotEqual(c.key(SHA, "fast"), c.key(SHA, "deep"))
        self.assertIn(f"_v{CACHE_VERSION}", c.key(SHA, "fast"))
        with self.assertRaises(ValueError):
            c.key("not-a-sha", "fast")

    def test_miss_then_hit(self):
        with tempfile.TemporaryDirectory() as td:
            c = AuditCache(td)
            self.assertIsNone(c.get(SHA, "fast"))
            path = c.put(fake_report("fast"))
            self.assertIsNotNone(path)
            self.assertTrue(path.is_file())
            hit = c.get(SHA, "fast")
            self.assertIsNotNone(hit)
            self.assertEqual(hit["basic_info"]["package_name"], "org.example")

    def test_modes_do_not_collide(self):
        with tempfile.TemporaryDirectory() as td:
            c = AuditCache(td)
            c.put(fake_report("fast"))
            self.assertIsNone(c.get(SHA, "deep"))

    def test_version_drift_invalidates(self):
        with tempfile.TemporaryDirectory() as td:
            c = AuditCache(td)
            c.put(fake_report("fast"))
            path = c._path(SHA, "fast")
            entry = json.loads(path.read_text(encoding="utf-8"))
            entry["cache_version"] = "old"
            path.write_text(json.dumps(entry), encoding="utf-8")
            self.assertIsNone(c.get(SHA, "fast"))

    def test_corrupt_entry_is_a_miss(self):
        with tempfile.TemporaryDirectory() as td:
            c = AuditCache(td)
            c.cache_dir.mkdir(parents=True, exist_ok=True)
            c._path(SHA, "fast").write_text("{broken", encoding="utf-8")
            self.assertIsNone(c.get(SHA, "fast"))

    def test_clear_removes_entries_only(self):
        with tempfile.TemporaryDirectory() as td:
            c = AuditCache(td)
            c.put(fake_report("fast"))
            c.put(fake_report("deep"))
            self.assertEqual(c.clear(), 2)
            self.assertEqual(c.clear(), 0)

    def test_rejects_incomplete_report(self):
        with tempfile.TemporaryDirectory() as td:
            c = AuditCache(td)
            self.assertIsNone(c.put({"audit_metadata": {"sha256": SHA}}))


class TestApplyCache(unittest.TestCase):
    def test_refreshes_timestamp_and_marks_hit(self):
        with tempfile.TemporaryDirectory() as td:
            apk = Path(td) / "app.apk"
            apk.write_bytes(b"fake apk payload")
            auditor = APKAuditor(str(apk), str(Path(td) / "out"), mode="fast")
            auditor.apply_cache(fake_report("fast"))
            meta = auditor.report["audit_metadata"]
            self.assertTrue(meta["cache"]["hit"])
            self.assertEqual(meta["cache"]["original_timestamp"], "2026-01-01T00:00:00Z")
            self.assertNotEqual(meta["timestamp"], "2026-01-01T00:00:00Z")
            md = auditor._generate_markdown()
            self.assertIn("**Cache:** HIT", md)


if __name__ == "__main__":
    unittest.main()
