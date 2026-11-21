#!/usr/bin/env python3
"""
APK Audit Engine - Comprehensive APK analysis using JADX and Androguard.
Generates Markdown and JSON reports.

Created and maintained by arifstia
https://github.com/arifstia/arm64-apk-workbench
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

class APKAuditor:
    """APK auditor with FAST / NORMAL / DEEP performance modes."""

    def __init__(self, apk_path: str, output_dir: str, mode: str = "normal"):
        self.apk_path = Path(apk_path).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.mode = mode if mode in ("fast", "normal", "deep") else "normal"
        self._timings: Dict[str, float] = {}
        self.report: Dict[str, Any] = {
            "audit_metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "apk_path": str(self.apk_path),
                "apk_name": self.apk_path.name,
                "mode": self.mode,
                "sha256": self._sha256(),
                "tool": "apk-workbench",
                "author": "arifstia",
            },
            "basic_info": {},
            "manifest": {},
            "permissions": [],
            "dex_info": {},
            "native_libraries": [],
            "resources": {},
            "certificates": [],
            "abi": [],
            "size_analysis": {},
        }

    def run_cmd(self, cmd: List[str], timeout: int = 300) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def _sha256(self) -> str:
        """Compute SHA-256 of the APK (used for cache keys and integrity)."""
        h = hashlib.sha256()
        with open(self.apk_path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def _timed(self, name: str, func) -> None:
        """Run a stage and record its wall-clock duration."""
        start = time.monotonic()
        func()
        self._timings[name] = round(time.monotonic() - start, 3)

    def get_apk_size(self) -> Dict[str, Any]:
        stat = self.apk_path.stat()
        with zipfile.ZipFile(self.apk_path, 'r') as zf:
            entries = zf.infolist()
            compressed = sum(e.compress_size for e in entries)
            uncompressed = sum(e.file_size for e in entries)
            return {
                "file_size_bytes": stat.st_size,
                "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
                "zip_entries": len(entries),
                "compressed_size_bytes": compressed,
                "uncompressed_size_bytes": uncompressed,
                "compression_ratio": round(compressed / uncompressed, 4) if uncompressed > 0 else 0,
            }

    def audit_basic_info(self) -> None:
        size_info = self.get_apk_size()
        self.report["size_analysis"] = size_info

        # aapt dump badging
        result = self.run_cmd(["aapt", "dump", "badging", str(self.apk_path)])
        if result.returncode == 0:
            self._parse_aapt_badging(result.stdout)

        # apksigner verify -print-certs
        result = self.run_cmd(["apksigner", "verify", "--print-certs", str(self.apk_path)])
        if result.returncode == 0:
            self._parse_apksigner_certs(result.stdout)

    def _parse_aapt_badging(self, output: str) -> None:
        info = self.report["basic_info"]
        for line in output.splitlines():
            if line.startswith("package:"):
                m = re.search(r"name='([^']+)'", line)
                if m: info["package_name"] = m.group(1)
                m = re.search(r"versionCode='(\d+)'", line)
                if m: info["version_code"] = int(m.group(1))
                m = re.search(r"versionName='([^']+)'", line)
                if m: info["version_name"] = m.group(1)
                m = re.search(r"platformBuildVersionName='([^']+)'", line)
                if m: info["platform_build_version"] = m.group(1)
            elif line.startswith("sdkVersion:"):
                info["min_sdk"] = line.split(":")[1].strip().strip("'")
            elif line.startswith("targetSdkVersion:"):
                info["target_sdk"] = line.split(":")[1].strip().strip("'")
            elif line.startswith("application:"):
                m = re.search(r"label='([^']*)'", line)
                if m: info["app_label"] = m.group(1)
                m = re.search(r"icon='([^']*)'", line)
                if m: info["app_icon"] = m.group(1)
            elif line.startswith("uses-permission:"):
                m = re.search(r"name='([^']+)'", line)
                if m: self.report["permissions"].append(m.group(1))
            elif line.startswith("uses-feature:"):
                m = re.search(r"name='([^']+)'", line)
                if m:
                    if "features" not in info: info["features"] = []
                    info["features"].append(m.group(1))
            elif line.startswith("locales:"):
                info["locales"] = line.split(":", 1)[1].strip()
            elif line.startswith("densities:"):
                info["densities"] = line.split(":", 1)[1].strip()
            elif line.startswith("native-code:"):
                abis = line.split(":", 1)[1].strip().split()
                self.report["abi"] = abis

    def _parse_apksigner_certs(self, output: str) -> None:
        certs = []
        current = {}
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("Signer #"):
                if current: certs.append(current)
                current = {"signer_index": len(certs) + 1}
            elif line.startswith("X.509"):
                m = re.search(r"Subject: (.+)", line)
                if m: current["subject"] = m.group(1).strip()
            elif "Digest:" in line:
                m = re.search(r"(\w+) Digest: (.+)", line)
                if m: current.setdefault("digests", {})[m.group(1)] = m.group(2).strip()
            elif line.startswith("Certificate:"):
                current["cert_raw"] = line
        if current: certs.append(current)
        self.report["certificates"] = certs

    def audit_manifest_with_androguard(self) -> None:
        try:
            venv_site = "/root/projects/apk-workbench/.venv/lib/python3.14/site-packages"
            import sys
            if venv_site not in sys.path:
                sys.path.insert(0, venv_site)
            from androguard.core.apk import APK
            apk = APK(str(self.apk_path))
            self.report["manifest"]["package"] = apk.get_package()
            self.report["manifest"]["version_name"] = apk.get_androidversion_name()
            self.report["manifest"]["version_code"] = apk.get_androidversion_code()
            self.report["manifest"]["min_sdk"] = apk.get_min_sdk_version()
            self.report["manifest"]["target_sdk"] = apk.get_target_sdk_version()
            self.report["manifest"]["max_sdk"] = apk.get_max_sdk_version()
            self.report["manifest"]["permissions"] = apk.get_permissions()
            self.report["manifest"]["activities"] = apk.get_activities()
            self.report["manifest"]["services"] = apk.get_services()
            self.report["manifest"]["receivers"] = apk.get_receivers()
            self.report["manifest"]["providers"] = apk.get_providers()
            self.report["manifest"]["uses_permissions"] = apk.get_uses_permissions()
            self.report["manifest"]["uses_features"] = apk.get_features()
            self.report["manifest"]["libraries"] = apk.get_libraries()
            self.report["manifest"]["declared_permissions"] = apk.get_declared_permissions()
        except Exception as e:
            self.report["manifest"]["androguard_error"] = str(e)

    def audit_dex_files(self) -> None:
        try:
            from androguard.core.apk import APK
            from androguard.core.dex import DEX
            apk = APK(str(self.apk_path))
            dex_files = []
            for i, dex_data in enumerate(apk.get_all_dex()):
                dex = DEX(dex_data)
                classes = list(dex.get_classes())
                dex_info = {
                    "index": i,
                    "classes_count": len(classes),
                    "methods_count": sum(len(cls.get_methods()) for cls in classes),
                    "fields_count": sum(len(cls.get_fields()) for cls in classes),
                    "strings_count": len(dex.get_strings()),
                }
                dex_files.append(dex_info)
            self.report["dex_info"]["files"] = dex_files
            self.report["dex_info"]["total_dex_count"] = len(dex_files)
        except Exception as e:
            self.report["dex_info"]["error"] = str(e)

    def audit_native_libraries(self) -> None:
        try:
            with zipfile.ZipFile(self.apk_path, 'r') as zf:
                libs = [f for f in zf.namelist() if f.startswith("lib/") and f.endswith(".so")]
                for lib in libs:
                    info = zf.getinfo(lib)
                    abi = lib.split("/")[1] if lib.count("/") > 1 else "unknown"
                    self.report["native_libraries"].append({
                        "path": lib,
                        "abi": abi,
                        "size_bytes": info.file_size,
                        "compressed_size": info.compress_size,
                    })
        except Exception as e:
            self.report["native_libraries"] = [{"error": str(e)}]

    def audit_resources(self) -> None:
        try:
            with zipfile.ZipFile(self.apk_path, 'r') as zf:
                res = [f for f in zf.namelist() if f.startswith("res/")]
                by_type: Dict[str, int] = {}
                for r in res:
                    parts = r.split("/")
                    if len(parts) >= 2:
                        by_type[parts[1]] = by_type.get(parts[1], 0) + 1
                self.report["resources"] = {
                    "total_files": len(res),
                    "by_type": by_type,
                }
        except Exception as e:
            self.report["resources"]["error"] = str(e)

    def run_jadx_summary(self, timeout: int = 600) -> None:
        """Run JADX decompilation summary. Longer timeout for large APKs on ARM64."""
        import shutil
        # Clean previous output
        shutil.rmtree("/tmp/jadx_summary", ignore_errors=True)
        try:
            result = self.run_cmd([
                "jadx", "--no-res", "--show-bad-code",
                "--output-dir", "/tmp/jadx_summary",
                str(self.apk_path)
            ], timeout=timeout)
            out_dir = Path("/tmp/jadx_summary")
            java_count = len(list(out_dir.rglob("*.java"))) if out_dir.is_dir() else 0
            if result.returncode == 0:
                self.report["jadx_decompile"] = f"success ({java_count} java files)"
            elif java_count > 0:
                # JADX exit 3 = "finished with errors" but classes were still
                # emitted. Report as partial instead of a hard failure.
                self.report["jadx_decompile"] = (
                    f"partial (exit {result.returncode}, {java_count} java files produced)"
                )
            else:
                err = result.stderr.strip() if result.stderr else "unknown error"
                self.report["jadx_decompile"] = f"failed (exit {result.returncode}): {err[:200]}"
        except subprocess.TimeoutExpired:
            self.report["jadx_decompile"] = f"timeout after {timeout}s (large APK, consider skipping with --skip-jadx)"
        except Exception as e:
            self.report["jadx_decompile"] = f"error: {str(e)[:200]}"

    def apply_cache(self, cached_report: Dict[str, Any]) -> None:
        """Adopt a cached report, refreshing timestamps and cache metadata."""
        original_ts = cached_report.get("audit_metadata", {}).get("timestamp", "unknown")
        self.report = cached_report
        self._timings = {}
        meta = self.report.setdefault("audit_metadata", {})
        meta["cache"] = {
            "hit": True,
            "original_timestamp": original_ts,
            "served_at": datetime.now(timezone.utc).isoformat() + "Z",
        }
        meta["timestamp"] = meta["cache"]["served_at"]

    def generate_reports(self) -> None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base = self.output_dir / f"audit_{self.apk_path.stem}_{timestamp}"

        # JSON report
        json_path = base.with_suffix(".json")
        with open(json_path, "w") as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)

        # Markdown report
        md_path = base.with_suffix(".md")
        with open(md_path, "w") as f:
            f.write(self._generate_markdown())

        print(f"Reports generated:")
        print(f"  JSON: {json_path}")
        print(f"  Markdown: {md_path}")

    def _generate_markdown(self) -> str:
        r = self.report
        meta = r.get("audit_metadata", {})
        basic = r.get("basic_info", {})
        manifest = r.get("manifest", {})
        perms = r.get("permissions", [])
        dex = r.get("dex_info", {})
        native = r.get("native_libraries", [])
        resources = r.get("resources", {})
        certs = r.get("certificates", [])
        abi = r.get("abi", [])
        size = r.get("size_analysis", {})

        md = []
        md.append(f"# APK Audit Report: {meta.get('apk_name', 'Unknown')}")
        md.append(f"**Generated:** {meta.get('timestamp', 'N/A')}")
        md.append(f"**APK Path:** {meta.get('apk_path', 'N/A')}")
        md.append(f"**Mode:** {meta.get('mode', 'normal')}  |  **SHA-256:** `{meta.get('sha256', 'N/A')}`")
        md.append(f"**Author:** {meta.get('author', 'arifstia')}")
        if r.get("timings_seconds"):
            md.append("**Timings (s):** " + ", ".join(f"{k}={v}" for k, v in r["timings_seconds"].items()))
        cache_info = meta.get("cache")
        if cache_info and cache_info.get("hit"):
            md.append(f"**Cache:** HIT (original run: {cache_info.get('original_timestamp', 'unknown')})")
        else:
            md.append("**Cache:** MISS (full analysis performed)")
        md.append("")

        md.append("## Basic Information")
        md.append(f"- **Package Name:** {basic.get('package_name', 'N/A')}")
        md.append(f"- **Version Name:** {basic.get('version_name', 'N/A')}")
        md.append(f"- **Version Code:** {basic.get('version_code', 'N/A')}")
        md.append(f"- **Min SDK:** {basic.get('min_sdk', 'N/A')}")
        md.append(f"- **Target SDK:** {basic.get('target_sdk', 'N/A')}")
        md.append(f"- **App Label:** {basic.get('app_label', 'N/A')}")
        md.append(f"- **Supported ABIs:** {', '.join(abi) if abi else 'N/A'}")
        md.append(f"- **Locales:** {basic.get('locales', 'N/A')}")
        md.append(f"- **Densities:** {basic.get('densities', 'N/A')}")
        md.append("")

        md.append("## Size Analysis")
        md.append(f"- **File Size:** {size.get('file_size_mb', 0)} MB ({size.get('file_size_bytes', 0)} bytes)")
        md.append(f"- **ZIP Entries:** {size.get('zip_entries', 0)}")
        md.append(f"- **Compressed Size:** {size.get('compressed_size_bytes', 0)} bytes")
        md.append(f"- **Uncompressed Size:** {size.get('uncompressed_size_bytes', 0)} bytes")
        md.append(f"- **Compression Ratio:** {size.get('compression_ratio', 0) * 100:.1f}%")
        md.append("")

        md.append("## Permissions (from aapt)")
        if perms:
            for p in perms:
                md.append(f"- `{p}`")
        else:
            md.append("*(none found)*")
        md.append("")

        md.append("## Manifest Details (Androguard)")
        if "error" in manifest:
            md.append(f"*Androguard error: {manifest['error']}*")
        else:
            md.append(f"- **Package:** {manifest.get('package', 'N/A')}")
            md.append(f"- **Version:** {manifest.get('version_name', 'N/A')} ({manifest.get('version_code', 'N/A')})")
            md.append(f"- **Min SDK:** {manifest.get('min_sdk', 'N/A')}")
            md.append(f"- **Target SDK:** {manifest.get('target_sdk', 'N/A')}")
            md.append(f"- **Activities:** {len(manifest.get('activities', []))}")
            md.append(f"- **Services:** {len(manifest.get('services', []))}")
            md.append(f"- **Receivers:** {len(manifest.get('receivers', []))}")
            md.append(f"- **Providers:** {len(manifest.get('providers', []))}")
            md.append(f"- **Declared Permissions:** {len(manifest.get('declared_permissions', []))}")
        md.append("")

        md.append("## DEX Analysis")
        if "error" in dex:
            md.append(f"*Error: {dex['error']}*")
        elif dex.get("mode") == "quick-count" or not dex.get("files"):
            md.append(f"- **Total DEX Files:** {dex.get('total_dex_count', 0)}")
            if dex.get("mode") == "quick-count":
                md.append("- *(quick count mode — run `--mode deep` for classes/methods/fields/strings)*")
                for d in dex.get("files", []):
                    md.append(f"  - **DEX {d['index']}:** `{d.get('name', 'N/A')}`")
        else:
            md.append(f"- **Total DEX Files:** {dex.get('total_dex_count', 0)}")
            for d in dex.get("files", []):
                md.append(f"  - **DEX {d['index']}:** {d.get('classes_count', '?')} classes, {d.get('methods_count', '?')} methods, {d.get('fields_count', '?')} fields, {d.get('strings_count', '?')} strings")
        md.append("")

        md.append("## Native Libraries")
        if native and "error" not in native[0]:
            for n in native:
                md.append(f"- `{n['path']}` (ABI: {n['abi']}, Size: {n['size_bytes']} bytes)")
        elif native:
            md.append(f"*Error: {native[0]['error']}*")
        else:
            md.append("*(none)*")
        md.append("")

        md.append("## Resources")
        if "error" in resources:
            md.append(f"*Error: {resources['error']}*")
        else:
            md.append(f"- **Total Resource Files:** {resources.get('total_files', 0)}")
            for typ, count in sorted(resources.get("by_type", {}).items()):
                md.append(f"  - **{typ}/**: {count}")
        md.append("")

        md.append("## Certificates")
        if certs:
            for c in certs:
                md.append(f"### Signer #{c.get('signer_index', '?')}")
                if "subject" in c: md.append(f"- **Subject:** {c['subject']}")
                for algo, digest in c.get("digests", {}).items():
                    md.append(f"- **{algo} Digest:** {digest}")
        else:
            md.append("*(none or unsigned)*")
        md.append("")

        md.append("---")
        md.append("*Report generated by apk-workbench audit engine*")
        return "\n".join(md)

    def run(self) -> Dict[str, Any]:
        print(f"[+] Auditing: {self.apk_path.name} (mode={self.mode})")
        print(f"    SHA-256: {self.report['audit_metadata']['sha256']}")

        # Basic info & certificates — always run in all modes (integrity check)
        print("[+] Basic info & certificates...")
        self._timed("basic_info", self.audit_basic_info)

        # Manifest — run in all modes (minimal in fast via Androguard still cheap)
        print("[+] Manifest (Androguard)...")
        self._timed("manifest", self.audit_manifest_with_androguard)

        # Native libraries & resources are lightweight (ZIP listing)
        print("[+] Native libraries...")
        self._timed("native_libraries", self.audit_native_libraries)

        if self.mode in ("normal", "deep"):
            print("[+] Resources...")
            self._timed("resources", self.audit_resources)

        if self.mode == "deep":
            print("[+] DEX files (deep)...")
            self._timed("dex", self.audit_dex_files)
            print("[+] JADX decompilation summary (this can take several minutes on ARM64)...")
            self._timed("jadx", lambda: self.run_jadx_summary(timeout=900))
        elif self.mode == "normal":
            # Lightweight DEX count from ZIP (no full Androguard parse)
            print("[+] DEX file count (normal)...")
            self._timed("dex", self._dex_count_quick)

        self.report["timings_seconds"] = self._timings
        print("[+] Generating reports...")
        self._timed("report", self.generate_reports)
        return self.report

    def _dex_count_quick(self) -> None:
        """Quickly count DEX files from the ZIP without full parse (normal mode)."""
        try:
            with zipfile.ZipFile(self.apk_path, "r") as zf:
                dex = [n for n in zf.namelist() if re.match(r"classes\d*\.dex$", n)]
            self.report["dex_info"]["files"] = [
                {"index": i, "name": name} for i, name in enumerate(sorted(dex))
            ]
            self.report["dex_info"]["total_dex_count"] = len(dex)
            self.report["dex_info"]["mode"] = "quick-count"
        except Exception as e:
            self.report["dex_info"]["error"] = str(e)


def main():
    if len(sys.argv) < 2:
        print("Usage: apk_audit.py <apk_path> [output_dir]")
        sys.exit(1)
    apk_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "/root/projects/apk-workbench/analysis"
    if not os.path.exists(apk_path):
        print(f"APK not found: {apk_path}")
        sys.exit(1)
    auditor = APKAuditor(apk_path, output_dir)
    auditor.run()


if __name__ == "__main__":
    main()