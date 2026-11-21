#!/usr/bin/env python3
"""
Portable smoke tests for ARM64 APK Workbench.

These tests deliberately avoid external Android tools so they can run on any
GitHub-hosted runner. The full ARM64 toolchain verification is documented in
reports/GITHUB_RELEASE_AUDIT.md and reports/PERFORMANCE_REPORT.md.

Run with:
    python3 -m unittest discover -s tests -p 'test_*.py' -v
"""
import argparse
import inspect
import sys
import tempfile
import typing
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import apk_audit  # noqa: E402
import apk_cache  # noqa: E402
import apk_patch  # noqa: E402
import apk_workbench as wb  # noqa: E402


def make_cli(**overrides):
    """Build a WorkbenchCLI instance with harmless defaults."""
    values = {
        "command": "doctor",
        "apk": None,
        "source": None,
        "output": None,
        "verbose": False,
        "mode": "normal",
        "no_cache": False,
    }
    values.update(overrides)
    return wb.WorkbenchCLI(argparse.Namespace(**values))


class TestAnnotationSafety(unittest.TestCase):
    def test_every_annotation_name_resolves(self):
        """Python 3.12 evaluates annotations eagerly; 3.14 defers them.

        Force resolution here so an unimported typing name fails locally too,
        instead of only breaking CI on older Python versions.
        """
        for mod in (wb, apk_audit, apk_cache, apk_patch):
            for name, obj in vars(mod).items():
                if getattr(obj, "__module__", None) != mod.__name__:
                    continue
                if inspect.isfunction(obj):
                    with self.subTest(module=mod.__name__, function=name):
                        typing.get_type_hints(obj)
                elif inspect.isclass(obj):
                    for mname, member in vars(obj).items():
                        if inspect.isfunction(member):
                            with self.subTest(module=mod.__name__, method=f"{name}.{mname}"):
                                typing.get_type_hints(member)


class TestBranding(unittest.TestCase):
    def test_version_is_defined(self):
        self.assertEqual(wb.VERSION, "1.1.0")

    def test_banner_has_author_and_repo(self):
        self.assertIn("arifstia", wb.BANNER)
        self.assertIn("arm64-apk-workbench", wb.BANNER)


class TestToolSelection(unittest.TestCase):
    def test_project_wrappers_are_preferred(self):
        cli = make_cli()
        self.assertTrue(cli._apktool().endswith("tools/bin/apktool"))
        self.assertTrue(cli._aapt2().endswith("tools/bin/aapt2"))

    def test_framework_detection(self):
        with tempfile.TemporaryDirectory() as td:
            cli = make_cli()
            cli.workspace = Path(td)
            self.assertIsNone(cli._framework_dir())
            fw = Path(td) / "tools" / "apktool" / "framework"
            fw.mkdir(parents=True)
            (fw / "1.apk").write_bytes(b"stub")
            self.assertEqual(cli._framework_dir(), fw)


class TestDollarResourceFix(unittest.TestCase):
    def test_renames_resources_and_references(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "decoded_app"
            drawable = src / "res" / "drawable"
            values = src / "res" / "values"
            drawable.mkdir(parents=True)
            values.mkdir(parents=True)

            (drawable / "$avd_hide__0.xml").write_text("<vector />", encoding="utf-8")
            (drawable / "avd_hide.xml").write_text(
                '<animated-vector android:drawable="@drawable/$avd_hide__0" />',
                encoding="utf-8",
            )
            (values / "public.xml").write_text(
                '<resources><public type="drawable" name="$avd_hide__0" id="0x7f080001" /></resources>',
                encoding="utf-8",
            )

            cli = make_cli()
            cli.workspace = Path(td)
            count = cli._fix_dollar_resources(src)

            self.assertEqual(count, 1)
            self.assertFalse((drawable / "$avd_hide__0.xml").exists())
            self.assertTrue((drawable / "_avd_hide__0.xml").exists())
            self.assertIn("@drawable/_avd_hide__0", (drawable / "avd_hide.xml").read_text())
            self.assertIn('name="_avd_hide__0"', (values / "public.xml").read_text())
            records = list((Path(td) / "patches").glob("dollar_resource_fix_*.json"))
            self.assertEqual(len(records), 1)

    def test_noop_on_plain_source(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "app"
            (src / "res").mkdir(parents=True)
            cli = make_cli()
            cli.workspace = Path(td)
            self.assertEqual(cli._fix_dollar_resources(src), 0)


class TestErrorHandling(unittest.TestCase):
    def test_audit_requires_apk(self):
        self.assertEqual(make_cli(apk=None).cmd_audit(), 1)

    def test_verify_requires_apk(self):
        self.assertEqual(make_cli(apk=None).cmd_verify(), 1)

    def test_build_requires_source(self):
        self.assertEqual(make_cli(source=None).cmd_build(), 1)

    def test_unknown_apk_path_fails(self):
        self.assertEqual(make_cli(apk="/definitely/not/here.apk").cmd_audit(), 1)


if __name__ == "__main__":
    unittest.main()
