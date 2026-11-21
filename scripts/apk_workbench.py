#!/usr/bin/env python3
"""
apk-workbench - Unified CLI for APK analysis and modification.

Created and maintained by arifstia
https://github.com/arifstia/arm64-apk-workbench
Copyright (c) 2026 arifstia
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

VERSION = "1.0.1"
AUTHOR = "arifstia"

BANNER = f"""apk-workbench v{VERSION}
ARM64 APK Analysis and Modification Toolkit
Created and maintained by {AUTHOR}
https://github.com/{AUTHOR}/arm64-apk-workbench"""


class WorkbenchCLI:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        # Resolve workspace relative to this script (parent of scripts/)
        self.workspace = Path(__file__).resolve().parent.parent
        self.logs_dir = self.workspace / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.logs_dir / f"cli_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"

    def log(self, message: str) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(self.log_file, "a") as f:
            f.write(f"{ts} | {message}\n")

    def run_cmd(self, cmd: List[str], timeout: Optional[int] = 900) -> subprocess.CompletedProcess:
        """Run a command with optional timeout. None = no timeout."""
        self.log(f"$ {' '.join(str(c) for c in cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        self.log(f"exit={result.returncode} stderr={result.stderr.strip()[:300]}")
        return result

    def _apktool(self) -> str:
        """Return project-local APKTool 3.x wrapper if present, else system apktool."""
        local = self.workspace / "tools" / "bin" / "apktool"
        if local.exists() and os.access(local, os.X_OK):
            return str(local)
        return "apktool"

    def _aapt2(self) -> str:
        """Return project-local ARM64 aapt2 wrapper if present, else system aapt2.

        APKTool 3.x bundles an x86_64 aapt2 which cannot execute on ARM64.
        The project wrapper filters unsupported flags and execs the native
        distro aapt2. Pass this via `apktool b --aapt`.
        """
        local = self.workspace / "tools" / "bin" / "aapt2"
        if local.exists() and os.access(local, os.X_OK):
            return str(local)
        return "aapt2"

    def _framework_dir(self) -> Path | None:
        """Return project-local APKTool framework directory if populated."""
        fw = self.workspace / "tools" / "apktool" / "framework"
        if fw.is_dir() and (fw / "1.apk").exists():
            return fw
        return None

    def _fix_dollar_resources(self, source_dir: Path) -> int:
        """Rename $-prefixed resources that aapt2 rejects as invalid entry names.

        Material Components emits names like `$mtrl_checkbox_button__0`.
        aapt2 refuses them, so before building we:
          1. rename files  $foo -> _foo
          2. update res/values/public.xml   name="$foo" -> name="_foo"
          3. update XML references  @drawable/$foo -> @drawable/_foo
        All changes are logged and a patch record is written to patches/.
        Returns the number of renamed resources (0 = nothing to do).
        """
        res_dir = source_dir / "res"
        if not res_dir.is_dir():
            return 0
        dollar_files = [p for p in res_dir.rglob("$*") if p.is_file()]
        if not dollar_files:
            return 0

        for p in dollar_files:
            new = p.with_name(p.name.replace("$", "_"))
            p.rename(new)

        # public.xml
        for pub in res_dir.rglob("public.xml"):
            try:
                s = pub.read_text(encoding="utf-8")
                s2 = s.replace('name="$', 'name="_')
                if s2 != s:
                    pub.write_text(s2, encoding="utf-8")
            except Exception as e:
                self.log(f"public.xml update failed: {e}")

        # XML references
        pattern = re.compile(r'(@[a-z]+[/:])\$')
        for xml in res_dir.rglob("*.xml"):
            try:
                s = xml.read_text(encoding="utf-8")
                s2 = pattern.sub(r'\1_', s)
                if s2 != s:
                    xml.write_text(s2, encoding="utf-8")
            except Exception as e:
                self.log(f"XML ref update failed: {e}")

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "source": str(source_dir),
            "action": "rename_dollar_prefixed_resources",
            "renamed_count": len(dollar_files),
            "reason": "aapt2 rejects resource entry names beginning with '$'",
            "author": AUTHOR,
        }
        patches_dir = self.workspace / "patches"
        patches_dir.mkdir(exist_ok=True)
        rec = patches_dir / f"dollar_resource_fix_{source_dir.name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        with open(rec, "w") as f:
            json.dump(record, f, indent=2)
        self.log(f"Renamed {len(dollar_files)} $-prefixed resources; record: {rec.name}")
        return len(dollar_files)

    def _require_tool(self, tool: str) -> bool:
        if tool == "apktool":
            return Path(self._apktool()).exists()
        if shutil.which(tool) is None:
            print(f"Error: required tool '{tool}' not found. Run 'apk-workbench doctor'.")
            return False
        return True

    # ------------------------------------------------------------------ doctor
    def cmd_doctor(self) -> int:
        """Check system dependencies and environment."""
        print("=== apk-workbench doctor ===")
        print(BANNER)
        print(f"Workspace: {self.workspace}\n")

        checks = [
            ("Architecture", ["uname", "-m"], None),
            ("OS", ["bash", "-c", ". /etc/os-release; echo $PRETTY_NAME"], None),
            ("Kernel", ["uname", "-r"], None),
            ("Java", ["java", "-version"], None),
            ("Python", ["python3", "--version"], None),
            ("Node.js", ["node", "--version"], None),
            ("OpenCode", ["opencode", "--version"], None),
            ("JADX", ["jadx", "--version"], None),
            ("APKTool", [self._apktool(), "--version"], None),
            ("apksigner", ["apksigner", "--version"], None),
            ("zipalign", ["which", "zipalign"], None),
            ("aapt", ["aapt", "version"], None),
            ("aapt2", ["aapt2", "version"], None),
            ("smali", ["smali", "--version"], None),
            ("baksmali", ["baksmali", "--version"], None),
            ("keytool", ["which", "keytool"], None),
            ("Androguard", [str(self.workspace / ".venv/bin/androguard"), "--version"], None),
            ("RAM", ["bash", "-c", "free -h | awk 'NR==2{print $2\" total, \"$7\" available\"}'"], None),
            ("Disk", ["bash", "-c", "df -h / | awk 'NR==2{print $4\" available\"}'"], None),
        ]

        failed = 0
        for name, cmd, _ in checks:
            try:
                result = self.run_cmd(cmd, timeout=60)
                if result.returncode == 0:
                    # java prints to stderr
                    out = (result.stdout.strip() or result.stderr.strip()).split("\n")[0]
                    print(f"[OK]   {name}: {out[:90]}")
                else:
                    print(f"[FAIL] {name}: {(result.stderr or result.stdout).strip().splitlines()[0] if (result.stderr or result.stdout).strip() else 'no output'}")
                    failed += 1
            except Exception as e:
                print(f"[FAIL] {name}: ERROR - {e}")
                failed += 1

        print()
        if failed == 0:
            print("All checks passed. Environment is ready.")
            return 0
        print(f"{failed} check(s) failed. See 'apk-workbench tools' for details.")
        return 1

    # ------------------------------------------------------------------- tools
    def cmd_tools(self) -> int:
        """List installed tools with versions."""
        print("=== Installed Tools ===")
        tools = {
            "Java": ["java", "-version"],
            "javac": ["javac", "-version"],
            "Python": ["python3", "--version"],
            "Node.js": ["node", "--version"],
            "OpenCode": ["opencode", "--version"],
            "JADX": ["jadx", "--version"],
            "APKTool": [self._apktool(), "--version"],
            "apksigner": ["apksigner", "--version"],
            "zipalign": ["which", "zipalign"],
            "aapt": ["aapt", "version"],
            "aapt2": ["aapt2", "version"],
            "smali": ["smali", "--version"],
            "baksmali": ["baksmali", "--version"],
            "Androguard": [str(self.workspace / ".venv/bin/androguard"), "--version"],
        }
        for name, cmd in tools.items():
            try:
                result = self.run_cmd(cmd, timeout=60)
                if result.returncode == 0:
                    out = (result.stdout.strip() or result.stderr.strip()).split("\n")[0]
                    print(f"{name}: {out[:110]}")
                else:
                    print(f"{name}: NOT FOUND")
            except Exception:
                print(f"{name}: ERROR")
        return 0

    # ------------------------------------------------------------------- audit
    def cmd_audit(self) -> int:
        """Run APK audit with FAST / NORMAL / DEEP mode."""
        if not self.args.apk:
            print("Error: APK path required. Usage: apk-workbench audit app.apk [--mode fast|normal|deep]")
            return 1
        apk_path = Path(self.args.apk).resolve()
        if not apk_path.exists():
            print(f"Error: APK not found: {apk_path}")
            return 1
        if apk_path.suffix.lower() != ".apk":
            print(f"Error: Input must be an .apk file, got: '{apk_path.suffix}'")
            return 1
        output_dir = Path(self.args.output).resolve() if self.args.output else (self.workspace / "analysis")
        mode = getattr(self.args, "mode", "normal") or "normal"
        sys.path.insert(0, str(self.workspace / "scripts"))
        try:
            from apk_audit import APKAuditor
            from apk_cache import AuditCache

            auditor = APKAuditor(str(apk_path), str(output_dir), mode=mode)
            use_cache = not getattr(self.args, "no_cache", False)
            cache = AuditCache(output_dir) if use_cache else None

            if cache is not None:
                sha256 = auditor.report["audit_metadata"]["sha256"]
                cached = cache.get(sha256, mode)
                if cached is not None:
                    print(f"[CACHE HIT] Reusing audit for {apk_path.name} (mode={mode})")
                    auditor.apply_cache(cached)
                    auditor.generate_reports()
                    return 0
                print("[CACHE MISS] Running full analysis...")

            auditor.run()
            if cache is not None:
                path = cache.put(auditor.report)
                if path:
                    print(f"[CACHE] Stored result: {path.name}")
            return 0
        except Exception as e:
            print(f"[-] Audit failed: {e}")
            self.log(f"audit failed: {e}")
            return 1

    # ------------------------------------------------------------------ decode
    def cmd_decode(self) -> int:
        """Decode APK resources and Smali (long-running on ARM64)."""
        if not self.args.apk:
            print("Error: APK path required. Usage: apk-workbench decode app.apk [-o output_dir]")
            return 1
        apk_path = Path(self.args.apk).resolve()
        if not apk_path.exists():
            print(f"Error: APK not found: {apk_path}")
            return 1
        if not self._require_tool("apktool"):
            return 1
        output_dir = Path(self.args.output).resolve() if self.args.output else (self.workspace / "decoded")
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        decoded_path = output_dir / f"decoded_{apk_path.stem}_{timestamp}"
        print(f"[+] Decoding {apk_path.name} (this can take ~14 min for 12MB APK on ARM64)...")
        try:
            result = self.run_cmd([self._apktool(), "d", "-f", "-o", str(decoded_path), str(apk_path)], timeout=1800)
            if result.returncode == 0 and (decoded_path / "apktool.yml").exists():
                print(f"[+] Decoded successfully: {decoded_path}")
                return 0
            # partial decode
            file_count = len(list(decoded_path.rglob("*"))) if decoded_path.exists() else 0
            print(f"[-] Decode failed or incomplete (exit {result.returncode}, {file_count} files, timeout=1800s)")
            print(f"    Partial output: {decoded_path}")
            print(f"    apktool stderr: {result.stderr.strip()[:400]}")
            return 1
        except subprocess.TimeoutExpired:
            file_count = len(list(decoded_path.rglob("*"))) if decoded_path.exists() else 0
            print(f"[!] Decode timed out after 1800s; partial output at {decoded_path} ({file_count} files)")
            return 1

    # ------------------------------------------------------------------- build
    def cmd_build(self) -> int:
        """Build, zipalign, sign and verify an APK from decoded source."""
        source_arg = self.args.source or self.args.apk
        if not source_arg:
            print("Error: source directory required. Usage: apk-workbench build -s decoded/decoded_app_TIMESTAMP")
            return 1
        source_dir = Path(source_arg).resolve()
        if not source_dir.is_dir():
            print(f"Error: source directory not found: {source_dir}")
            return 1
        if not (source_dir / "apktool.yml").exists():
            print(f"Error: invalid decoded source (apktool.yml missing): {source_dir}")
            return 1
        for tool in ("apktool", "zipalign", "apksigner", "keytool"):
            if not self._require_tool(tool):
                return 1

        build_dir = self.workspace / "build"
        output_dir = self.workspace / "output"
        keys_dir = build_dir / "keys"
        for d in (build_dir, output_dir, keys_dir):
            d.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unsigned = build_dir / f"unsigned_{source_dir.name}_{timestamp}.apk"
        aligned = build_dir / f"aligned_{source_dir.name}_{timestamp}.apk"
        final = output_dir / f"signed_{source_dir.name}_{timestamp}.apk"
        keystore = keys_dir / "test_key.jks"
        alias, password = "test_key", "testkey"

        timings = {}
        # 0) compatibility: rename $-prefixed resources aapt2 rejects
        fixed = self._fix_dollar_resources(source_dir)
        if fixed:
            print(f"    Compatibility: renamed {fixed} $-prefixed resources (recorded in patches/)")

        # 1) apktool build
        print("[1/5] Building APK with apktool...")
        t = time.monotonic()
        build_cmd = [self._apktool(), "b", "-f", "--aapt", self._aapt2()]
        fw = self._framework_dir()
        if fw:
            build_cmd += ["-p", str(fw)]
        build_cmd += ["-o", str(unsigned), str(source_dir)]
        result = self.run_cmd(build_cmd, timeout=1800)
        timings["apktool_build"] = round(time.monotonic() - t, 2)
        if result.returncode != 0 or not unsigned.exists():
            print(f"[-] apktool build failed (exit {result.returncode}): {result.stderr.strip()[:500]}")
            return 1
        print(f"    OK ({timings['apktool_build']}s): {unsigned.name}")

        # 2) generate test keystore if missing
        if not keystore.exists():
            print("[2/5] Generating test keystore...")
            result = self.run_cmd([
                "keytool", "-genkeypair", "-v", "-keystore", str(keystore),
                "-alias", alias, "-keyalg", "RSA", "-keysize", "2048",
                "-validity", "365", "-storepass", password, "-keypass", password,
                "-dname", "CN=APK Workbench Test Key, OU=Dev, O=APK Workbench, L=NA, S=NA, C=ID",
            ], timeout=120)
            if result.returncode != 0:
                print(f"[-] Keystore generation failed: {result.stderr.strip()[:400]}")
                return 1
            shutil.copy2(keystore, self.workspace / "config" / "test.keystore")
        else:
            print("[2/5] Using existing test keystore.")

        # 3) zipalign
        print("[3/5] Zipaligning (4-byte alignment)...")
        t = time.monotonic()
        result = self.run_cmd(["zipalign", "-f", "4", str(unsigned), str(aligned)], timeout=300)
        timings["zipalign"] = round(time.monotonic() - t, 2)
        if result.returncode != 0 or not aligned.exists():
            print(f"[-] zipalign failed: {result.stderr.strip()[:400]}")
            return 1
        print(f"    OK ({timings['zipalign']}s)")

        # 4) apksigner sign
        print("[4/5] Signing with test key...")
        t = time.monotonic()
        result = self.run_cmd([
            "apksigner", "sign", "--ks", str(keystore),
            "--ks-key-alias", alias, "--ks-pass", f"pass:{password}",
            "--key-pass", f"pass:{password}", "--out", str(final), str(aligned),
        ], timeout=300)
        timings["apksigner"] = round(time.monotonic() - t, 2)
        if result.returncode != 0 or not final.exists():
            print(f"[-] apksigner failed: {result.stderr.strip()[:400]}")
            return 1
        print(f"    OK ({timings['apksigner']}s)")

        # 5) verify — never claim success before verification
        print("[5/5] Verifying signature...")
        result = self.run_cmd(["apksigner", "verify", "--verbose", "--print-certs", str(final)], timeout=300)
        if result.returncode != 0:
            print(f"[-] Verification FAILED (exit {result.returncode}): {result.stderr.strip()[:400]}")
            return 1
        print("    Signature VALID")

        sha = hashlib.sha256(final.read_bytes()).hexdigest()
        build_report = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "source": str(source_dir),
            "unsigned_apk": str(unsigned),
            "aligned_apk": str(aligned),
            "final_apk": str(final),
            "signature": "valid",
            "sha256": sha,
            "timings_seconds": timings,
            "author": AUTHOR,
        }
        report_path = self.workspace / "build" / f"build_report_{timestamp}.json"
        with open(report_path, "w") as f:
            json.dump(build_report, f, indent=2)
        print(f"\n[+] Build COMPLETE and VERIFIED: {final}")
        print(f"    SHA-256: {sha}")
        print(f"    Report: {report_path}")
        return 0

    # ------------------------------------------------------------------ backup
    def cmd_backup(self) -> int:
        """Create a timestamped backup of an APK."""
        if not self.args.apk:
            print("Error: APK path required. Usage: apk-workbench backup app.apk")
            return 1
        apk_path = Path(self.args.apk).resolve()
        if not apk_path.exists():
            print(f"Error: APK not found: {apk_path}")
            return 1
        backup_dir = self.workspace / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{apk_path.stem}_{timestamp}{apk_path.suffix}"
        shutil.copy2(apk_path, backup_path)
        sha = hashlib.sha256(backup_path.read_bytes()).hexdigest()
        print(f"[+] Backup created: {backup_path}")
        print(f"    SHA-256: {sha}")
        self.log(f"backup {apk_path} -> {backup_path}")
        return 0

    # ------------------------------------------------------------------ verify
    def cmd_verify(self) -> int:
        """Verify APK signature and print certificates."""
        if not self.args.apk:
            print("Error: APK path required. Usage: apk-workbench verify app.apk")
            return 1
        apk_path = Path(self.args.apk).resolve()
        if not apk_path.exists():
            print(f"Error: APK not found: {apk_path}")
            return 1
        if not self._require_tool("apksigner"):
            return 1
        result = self.run_cmd(["apksigner", "verify", "--verbose", "--print-certs", str(apk_path)], timeout=300)
        if result.returncode == 0:
            print("[OK] APK signature is VALID")
            print(result.stdout.strip() or result.stderr.strip())
            return 0
        print("[FAIL] APK signature is INVALID (or APK is unsigned)")
        print((result.stderr or result.stdout).strip()[:600])
        return 1

    # ------------------------------------------------------------------- patch
    def cmd_patch(self) -> int:
        """Create a patch record documenting modifications to decoded sources."""
        source_arg = self.args.source or self.args.apk
        if not source_arg:
            print("Error: source directory required. Usage: apk-workbench patch -s decoded/decoded_app_TIMESTAMP")
            return 1
        source_dir = Path(source_arg).resolve()
        if not source_dir.is_dir():
            print(f"Error: source directory not found: {source_dir}")
            return 1
        patch_dir = self.workspace / "patches"
        patch_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        patch_path = patch_dir / f"patch_{source_dir.name}_{timestamp}.json"

        # Snapshot file hashes of relevant editable files for change tracking
        snapshot = {}
        for pattern in ("AndroidManifest.xml", "smali/**/*.smali", "res/**/*", "unknown/**/*"):
            for p in source_dir.glob(pattern):
                if p.is_file():
                    try:
                        snapshot[str(p.relative_to(source_dir))] = hashlib.sha256(p.read_bytes()).hexdigest()
                    except Exception:
                        pass
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "source": str(source_dir),
            "description": getattr(self.args, "output", "") or "Manual modifications (documented via patch command)",
            "file_count": len(snapshot),
            "files": snapshot,
            "author": AUTHOR,
        }
        with open(patch_path, "w") as f:
            json.dump(record, f, indent=2)
        print(f"[+] Patch record created: {patch_path}")
        print(f"    Tracked {len(snapshot)} files. Review and edit the record to describe your changes.")
        return 0

    # --------------------------------------------------------------------- run
    def run(self) -> int:
        commands = {
            "doctor": self.cmd_doctor,
            "tools": self.cmd_tools,
            "audit": self.cmd_audit,
            "decode": self.cmd_decode,
            "analyze": self.cmd_audit,
            "backup": self.cmd_backup,
            "build": self.cmd_build,
            "verify": self.cmd_verify,
            "patch": self.cmd_patch,
        }
        return commands[self.args.command]()


def main():
    parser = argparse.ArgumentParser(
        prog="apk-workbench",
        description=BANNER,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  doctor    Check system dependencies and environment
  tools     List installed tools with versions
  audit     Audit APK (--mode fast|normal|deep; default normal)
  decode    Decode APK resources and Smali (~14 min for 12MB on ARM64)
  analyze   Alias for audit
  backup    Create timestamped backup of APK
  build     Build + zipalign + sign + verify from decoded source (-s DIR)
  verify    Verify APK signature and print certificates
  patch     Record a snapshot of modifications in decoded source (-s DIR)

Performance modes (audit):
  fast      Metadata, certificate & manifest only; quick DEX count
  normal    Adds resource analysis and quick DEX count (default)
  deep      Full DEX analysis + JADX decompilation summary

Audit caching:
  Results are cached per APK SHA-256 + mode in analysis/.cache/ (deep audits
  become near-instant on repeat). Use --no-cache to force a full run.

Examples:
  apk-workbench doctor
  apk-workbench audit app.apk --mode fast
  apk-workbench audit app.apk --mode deep
  apk-workbench decode app.apk
  apk-workbench backup app.apk
  apk-workbench build -s decoded/decoded_app_20261121_030938
  apk-workbench verify output/signed_app_20261121_030938.apk
"""
    )
    parser.add_argument("--version", action="version", version=f"apk-workbench {VERSION} (by {AUTHOR})")
    parser.add_argument("command", choices=[
        "doctor", "tools", "audit", "decode", "analyze", "backup", "build", "verify", "patch"
    ], help="Command to execute")
    parser.add_argument("apk", nargs="?", help="Path to APK file")
    parser.add_argument("-s", "--source", help="Source directory for build/patch commands")
    parser.add_argument("-o", "--output", help="Output directory / patch description")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--mode", choices=["fast", "normal", "deep"], default="normal",
                        help="Performance mode for audit (default: normal)")
    parser.add_argument("--no-cache", action="store_true",
                        help="Force a full audit, ignoring any cached result")
    args = parser.parse_args()
    cli = WorkbenchCLI(args)
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
