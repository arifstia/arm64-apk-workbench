#!/usr/bin/env python3
"""
APK Build/Decode Engine - Handles decoding, backing up, and building APKs.
"""
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

class APKBuilder:
    def __init__(self, apk_path: str, output_dir: str):
        self.apk_path = Path(apk_path).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir = self.output_dir / "backup"
        self.decoded_dir = self.output_dir / "decoded"
        self.build_dir = self.output_dir / "build"
        self.reports_dir = self.output_dir / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.decoded_dir.mkdir(parents=True, exist_ok=True)
        self.build_dir.mkdir(parents=True, exist_ok=True)
        self.report: Dict[str, Any] = {
            "audit_metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "apk_path": str(self.apk_path),
                "apk_name": self.apk_path.name,
            },
            "status": [],
            "backup": {},
            "decoding": {},
            "building": {},
            "verification": {},
        }

    def run_cmd(self, cmd: List[str], timeout: int = 300) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def backup_apk(self) -> Dict[str, Any]:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{self.apk_path.stem}_{timestamp}_{self.apk_path.suffix}"
        shutil.copy2(self.apk_path, backup_path)
        self.report["backup"] = {
            "original_path": str(self.apk_path),
            "backup_path": str(backup_path),
            "timestamp": timestamp,
            "status": "success",
        }
        return self.report["backup"]

    def decode_apk(self) -> Dict[str, Any]:
        self.decoded_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        decoded_path = self.decoded_dir / f"decoded_{self.apk_path.stem}_{timestamp}"
        decoded_path.mkdir(parents=True, exist_ok=True)
        try:
            self.run_cmd(["apktool", "d", "-f", "-o", str(decoded_path), str(self.apk_path)])
            self.report["decoding"] = {
                "decoded_path": str(decoded_path),
                "status": "success",
                "apktool_version": self.run_cmd(["apktool", "--version"]).stdout.strip().split()[-1],
            }
        except Exception as e:
            self.report["decoding"] = {
                "status": "failed",
                "error": str(e),
            }
        return self.report["decoding"]

    def build_apk(self) -> Dict[str, Any]:
        self.build_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        build_path = self.build_dir / f"rebuild_{self.apk_path.stem}_{timestamp}.apk"
        try:
            self.run_cmd(["apktool", "b", "-f", "-o", str(build_path), str(self.decoded_dir)])
            self.report["building"] = {
                "apk_path": str(build_path),
                "status": "success",
                "apktool_version": self.run_cmd(["apktool", "--version"]).stdout.strip().split()[-1],
            }
            return self.report["building"]
        except Exception as e:
            self.report["building"] = {
                "status": "failed",
                "error": str(e),
            }
            return self.report["building"]
        return self.report["building"]

    def zipalign_apk(self, apk_path: str) -> Dict[str, Any]:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        aligned_path = self.build_dir / f"aligned_{self.apk_path.stem}_{timestamp}.apk"
        aligned_timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        aligned_path = self.build_dir / f"aligned_{self.apk_path.stem}_{aligned_timestamp}.apk"
        try:
            self.run_cmd(["zipalign", "-v", "4", str(apk_path), str(aligned_path)])
            self.report["verification"] = {
                "status": "success",
                "aligned_apk": str(aligned_path),
                "zipalign_status": "success",
            }
            return self.report["verification"]
        except Exception as e:
            self.report["verification"] = {
                "status": "failed",
                "error": str(e),
            }
            return self.report["verification"]

    def sign_apk(self, apk_path: str) -> Dict[str, Any]:
        # Create test key if not exists
        key_dir = self.build_dir / "keys"
        key_dir.mkdir(parents=True, exist_ok=True)
        test_key = key_dir / "test_key.jks"
        test_key_alias = "test_key"
        test_key_pw = "testkey"
        if not key_dir / "test_key.jks".exists():
            self.run_cmd([
                "keytool", "genkey", "-v",
                "-keystore", str(test_key),
                "-alias", test_key_alias,
                "-keyalg", "RSA",
                "-keysize", "2048",
                "-validity", "365",
                "-keypass", test_key_pw,
                "-storepass", test_key_pw,
                "-dname", "CN=Test Key, OU=Test, O=Test, L=Test, S=Test, C=US",
            ], timeout=60)
        try:
            self.run_cmd([
                "apksigner", "sign",
                "--ks", str(test_key),
                "--ks-key-alias", test_key_alias,
                "--ks-pass", f"pass:{test_key_pw}",
                "--apks-pass", f"pass:{test_key_pw}",
                "--out", str(apk_path),
                str(apk_path),
            ])
            self.report["verification"] = {
                "status": "success",
                "signed_apk": str(apk_path),
                "signing_status": "success",
            }
            return self.report["verification"]
        except Exception as e:
            self.report["verification"] = {
                "status": "failed",
                "error": str(e),
            }
            return self.report["verification"]

    def verify_apk(self, apk_path: str) -> Dict[str, Any]:
        try:
            result = self.run_cmd([
                "apksigner", "verify",
                "--verbose",
                "--print-certs",
                str(apk_path)
            ])
            if result.returncode == 0:
                self.report["verification"] = {
                    "status": "success",
                    "verification_result": "valid",
                    "apk_path": str(apk_path),
                }
                return self.report["verification"]
            else:
                self.report["verification"] = {
                    "status": "failed",
                    "verification_result": "invalid",
                    "error": result.stderr.strip(),
                    "apk_path": str(apk_path),
                }
                return self.report["verification"]
        except Exception as e:
            self.report["verification"] = {
                "status": "failed",
                "error": str(e),
                "apk_path": str(apk_path),
            }
            return self.report["verification"]

    def generate_reports(self) -> None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base = self.reports_dir / f"apk_{self.apk_path.stem}_{timestamp}"
        # JSON report
        json_path = base.with_suffix(".json")
        with open(json_path, "w") as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        # Markdown report
        md_path = base.with_suffix(".md")
        with open(md_path, "w") as f:
            f.write(self._generate_markdown())
        print(f"[+] Reports generated:")
        print(f"  JSON: {json_path}")
        print(f"  Markdown: {md_path}")

    def _generate_markdown(self) -> str:
        r = self.report
        meta = r.get("audit_metadata", {})
        status = r.get("status", [])
        backup = r.get("backup", {})
        decoding = r.get("decoding", {})
        building = r.get("building", {})
        verification = r.get("verification", {})

        md = []
        md.append(f"# APK Build/Decode Report: {meta.get('apk_name', 'Unknown')}")
        md.append(f"**Generated:** {meta.get('timestamp', 'N/A')}")
        md.append(f"**APK Path:** {meta.get('apk_path', 'N/A')}")
        md.append("")

        md.append("## Backup")
        if backup.get("status") == "success":
            md.append(f"- **Status:** Success")
            md.append(f"- **Backup Path:** {backup.get('backup_path', 'N/A')}")
            md.append(f"- **Timestamp:** {backup.get('timestamp', 'N/A')}")
        else:
            md.append(f"- **Status:** Failed")
            md.append(f"- **Error:** {backup.get('error', 'N/A')}")
        md.append("")

        md.append("## Decoding")
        if decoding.get("status") == "success":
            md.append(f"- **Status:** Success")
            md.append(f"- **Decoded Path:** {decoding.get('decoded_path', 'N/A')}")
            md.append(f"- **APKTool Version:** {decoding.get('apktool_version', 'N/A')}")
        else:
            md.append(f"- **Status:** Failed")
            md.append(f"- **Error:** {decoding.get('error', 'N/A')}")
        md.append("")

        md.append("## Building")
        if building.get("status") == "success":
            md.append(f"- **Status:** Success")
            md.append(f"- **APK Path:** {building.get('apk_path', 'N/A')}")
            md.append(f"- **APKTool Version:** {building.get('apktool_version', 'N/A')}")
        else:
            md.append(f"- **Status:** Failed")
            md.append(f"- **Error:** {building.get('error', 'N/A')}")
        md.append("")

        md.append("## Verification")
        if verification.get("status") == "success" and verification.get("aligned_apk"):
            md.append(f"- **Status:** Success")
            md.append(f"- **Aligned APK:** {verification.get('aligned_apk', 'N/A')}")
            md.append(f"- **Status:** Success")
        elif verification.get("status") == "success":
            md.append(f"- **Status:** Success (Signed)")
            md.append(f"- **Signed APK:** {verification.get('signed_apk', 'N/A')}")
        else:
            md.append(f"- **Status:** Failed")
            md.append(f"- **Error:** {verification.get('error', 'N/A')}")
        md.append("")

        md.append("## Verification Result")
        if verification.get("status") == "success" and verification.get("verification_result") == "valid":
            md.append("✓ **Verification Result: VALID**")
        elif verification.get("status") == "success":
            md.append("✓ **Verification Result: SIGNED**")
        else:
            md.append(f"✗ **Verification Result: INVALID**")
            md.append(f"- **Error:** {verification.get('error', 'N/A')}")
        md.append("")

        md.append("---")
        md.append("*Report generated by apk-workbench build engine*")
        return "\n".join(md)

    def run(self) -> Dict[str, Any]:
        print(f"[+] Starting build process for: {self.apk_path.name}")
        print("[+] Backup...")
        self.backup_apk()
        print("[+] Decoding...")
        dec = self.decode_apk()
        if dec.get("status") != "success":
            self.generate_reports()
            return self.report
        print("[+] Building...")
        bld = self.build_apk()
        if bld.get("status") != "success":
            self.generate_reports()
            return self.report
        apk = bld["apk_path"]
        print("[+] Zipaligning...")
        self.zipalign_apk(apk)
        print("[+] Signing...")
        self.sign_apk(apk)
        print("[+] Verifying...")
        self.verify_apk(apk)
        print("[+] Generating reports...")
        self.generate_reports()
        return self.report


def main():
    if len(sys.argv) < 2:
        print("Usage: apk_build.py <apk_path> [output_dir]")
        sys.exit(1)
    apk_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "/root/projects/apk-workbench/output"
    if not os.path.exists(apk_path):
        print(f"APK not found: {apk_path}")
        sys.exit(1)
    builder = APKBuilder(apk_path, output_dir)
    builder.run()


if __name__ == "__main__":
    main()