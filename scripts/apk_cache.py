#!/usr/bin/env python3
"""
Audit result cache for ARM64 APK Workbench.

Caching is keyed by the SHA-256 of the APK, the audit mode and a schema version.
A deep audit of a 12 MB APK takes ~80 s on ARM64; a cache hit avoids repeating
JADX decompilation while still producing fresh, timestamped report files.

Cache entries are local artefacts and are gitignored. Use `--no-cache` to force
a full run, or delete `analysis/.cache/` to clear everything.

Created and maintained by arifstia
https://github.com/arifstia/arm64-apk-workbench
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Bump this when the report schema or any analysis stage changes, so old
# entries can never be served as if they were produced by the current engine.
CACHE_VERSION = "1"


class AuditCache:
    """Filesystem-backed cache for completed audit reports."""

    def __init__(self, output_dir: str | Path):
        self.output_dir = Path(output_dir).resolve()
        self.cache_dir = self.output_dir / ".cache"

    def key(self, sha256: str, mode: str) -> str:
        """Return a deterministic, filesystem-safe cache key."""
        clean_sha = "".join(ch for ch in str(sha256).lower() if ch in "0123456789abcdef")
        clean_mode = mode if mode in ("fast", "normal", "deep") else "normal"
        if len(clean_sha) != 64:
            raise ValueError("sha256 must be a 64-character hex digest")
        return f"audit_{clean_sha}_{clean_mode}_v{CACHE_VERSION}"

    def _path(self, sha256: str, mode: str) -> Path:
        return self.cache_dir / f"{self.key(sha256, mode)}.json"

    def get(self, sha256: str, mode: str) -> Optional[Dict[str, Any]]:
        """Return the cached report, or None on miss/corruption/version drift."""
        path = self._path(sha256, mode)
        if not path.is_file():
            return None
        try:
            with open(path, encoding="utf-8") as f:
                entry = json.load(f)
            if entry.get("cache_version") != CACHE_VERSION:
                return None
            if entry.get("sha256") != sha256.lower():
                return None
            if entry.get("mode") != mode:
                return None
            report = entry.get("report")
            if not isinstance(report, dict):
                return None
            if "audit_metadata" not in report or "basic_info" not in report:
                return None
            return report
        except (OSError, ValueError, TypeError):
            return None

    def put(self, report: Dict[str, Any]) -> Optional[Path]:
        """Store a completed report. Returns the path written, or None if invalid."""
        meta = report.get("audit_metadata", {})
        sha256 = meta.get("sha256")
        mode = meta.get("mode", "normal")
        if not sha256 or "basic_info" not in report:
            return None
        try:
            key = self.key(sha256, mode)
        except ValueError:
            return None

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "cache_version": CACHE_VERSION,
            "sha256": sha256.lower(),
            "mode": mode,
            "cached_at": datetime.now(timezone.utc).isoformat() + "Z",
            "report": report,
        }
        path = self.cache_dir / f"{key}.json"
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2, ensure_ascii=False)
        tmp.replace(path)
        return path

    def clear(self) -> int:
        """Remove all cache entries. Returns the number of files removed."""
        if not self.cache_dir.is_dir():
            return 0
        removed = 0
        for path in self.cache_dir.glob("audit_*_v*.json"):
            path.unlink()
            removed += 1
        return removed
