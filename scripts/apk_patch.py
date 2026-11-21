#!/usr/bin/env python3
"""
Patch management for decoded APK sources.

A patch snapshot copies the editable files of a decoded APK into
`patches/snapshots/<id>/files/`. That makes it possible to inspect what changed,
roll back to the exact baseline, or export the edits as a bundle that can be
applied to another decoded source tree.

Safety rules (enforced here):
  * nothing is ever deleted — replaced/removed files are moved to backup/
  * every overwrite is preceded by a backup
  * relative paths are validated against traversal
  * symlinks are never followed
  * --dry-run never writes

Created and maintained by arifstia
https://github.com/arifstia/arm64-apk-workbench
"""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PATCH_SCHEMA = "1"
AUTHOR = "arifstia"
EDITABLE_PATTERNS = ("AndroidManifest.xml", "smali/**/*.smali", "res/**/*", "unknown/**/*")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_rel(rel: str) -> Path:
    """Reject absolute paths and traversal before touching the filesystem."""
    if not isinstance(rel, str) or not rel.strip() or rel in (".", "./"):
        raise ValueError(f"unsafe relative path in patch record: {rel!r}")
    p = Path(rel)
    if p.is_absolute() or ".." in p.parts or "\\" in rel:
        raise ValueError(f"unsafe relative path in patch record: {rel!r}")
    return p


def collect_files(source_dir: Path) -> Dict[str, Path]:
    """Return {relative_path: absolute_path} for all editable regular files."""
    result: Dict[str, Path] = {}
    for pattern in EDITABLE_PATTERNS:
        for p in source_dir.glob(pattern):
            if p.is_symlink() or not p.is_file():
                continue
            result[p.relative_to(source_dir).as_posix()] = p
    return dict(sorted(result.items()))


class PatchManager:
    def __init__(self, patches_dir: str | Path, backup_dir: Optional[str | Path] = None,
                 workspace: Optional[str | Path] = None):
        self.patches_dir = Path(patches_dir).resolve()
        self.snapshots_dir = self.patches_dir / "snapshots"
        self.workspace = Path(workspace).resolve() if workspace else self.patches_dir.parent
        self.backup_dir = Path(backup_dir).resolve() if backup_dir else (self.workspace / "backup")

    # ---------------------------------------------------------------- helpers
    def _write_record(self, path: Path, record: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
        tmp.replace(path)

    def load(self, record_path: str | Path) -> Dict[str, Any]:
        path = Path(record_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"patch record not found: {path}")
        with open(path, encoding="utf-8") as f:
            record = json.load(f)
        if not isinstance(record, dict) or "files" not in record:
            raise ValueError(f"invalid patch record: {path}")
        if "id" not in record:
            raise ValueError("this is a legacy hash-only record — create a new snapshot to enable rollback")
        return record

    def list_records(self) -> List[Dict[str, Any]]:
        """Return all patch records, newest first."""
        if not self.patches_dir.is_dir():
            return []
        records: List[Dict[str, Any]] = []
        for path in sorted(self.patches_dir.glob("patch_*.json"), reverse=True):
            try:
                rec = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(rec, dict) and "id" in rec:
                    rec["_path"] = str(path)
                    records.append(rec)
            except (OSError, ValueError):
                continue
        return records

    def latest_for(self, source_dir: Path, kind: Optional[str] = None) -> Dict[str, Any]:
        """Return the newest record for a source directory."""
        source = Path(source_dir).resolve()
        for rec in self.list_records():
            if Path(rec.get("source", "")).resolve() != source:
                continue
            if kind and rec.get("kind") != kind:
                continue
            return rec
        raise FileNotFoundError(f"no patch record found for source: {source}")

    def _has_content(self, record: Dict[str, Any]) -> Path:
        """Return the content directory for a snapshot/bundle record."""
        content = record.get("content_dir")
        if not content:
            raise ValueError("this record has no file content — legacy hash-only records cannot be restored")
        path = Path(content)
        if not path.is_absolute():
            path = self.patches_dir / path
        if not path.is_dir():
            raise FileNotFoundError(f"patch content directory missing: {path}")
        return path

    def _backup_target(self, target: Path, source_dir: Path, label: str) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        dest_root = self.backup_dir / f"{label}_{stamp}"
        dest = dest_root / target.relative_to(source_dir)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(target), str(dest))
        return dest

    # ----------------------------------------------------------------- create
    def create(self, source_dir: Path, description: str = "") -> Dict[str, Any]:
        source_dir = Path(source_dir).resolve()
        if not source_dir.is_dir():
            raise NotADirectoryError(f"source directory not found: {source_dir}")
        files = collect_files(source_dir)
        stamp = datetime.now(timezone.utc)
        base_id = f"{source_dir.name}_{stamp.strftime('%Y%m%d_%H%M%S')}"
        sid, record_path = base_id, self.patches_dir / f"patch_{base_id}.json"
        counter = 2
        while record_path.exists():
            sid = f"{base_id}_{counter}"
            record_path = self.patches_dir / f"patch_{sid}.json"
            counter += 1
        content_dir = self.snapshots_dir / sid / "files"

        hashes: Dict[str, str] = {}
        for rel, path in files.items():
            dest = content_dir / safe_rel(rel)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            hashes[rel] = sha256_file(path)

        record = {
            "schema": PATCH_SCHEMA,
            "id": sid,
            "kind": "snapshot",
            "timestamp": stamp.isoformat() + "Z",
            "source": str(source_dir),
            "description": description or "Baseline snapshot of decoded source",
            "content_dir": f"snapshots/{sid}/files",
            "file_count": len(hashes),
            "files": hashes,
            "author": AUTHOR,
        }
        self._write_record(record_path, record)
        return record

    # ------------------------------------------------------------------- diff
    def diff(self, source_dir: Path, record: Dict[str, Any]) -> Dict[str, List[str]]:
        source_dir = Path(source_dir).resolve()
        current = collect_files(source_dir)
        baseline = set(record.get("files", {}).keys())
        now = set(current.keys())
        return {
            "added": sorted(now - baseline),
            "deleted": sorted(baseline - now),
            "modified": sorted(
                rel for rel in (now & baseline)
                if sha256_file(current[rel]) != record["files"][rel]
            ),
        }

    # --------------------------------------------------------------- rollback
    def rollback(self, source_dir: Path, record: Dict[str, Any],
                 dry_run: bool = False) -> Dict[str, Any]:
        source_dir = Path(source_dir).resolve()
        content_dir = self._has_content(record)
        current = collect_files(source_dir)
        result: Dict[str, Any] = {
            "restored": [], "backed_up": [], "removed_from_source": [], "dry_run": dry_run,
        }

        for rel, expected_hash in record.get("files", {}).items():
            rel_path = safe_rel(rel)
            baseline = content_dir / rel_path
            if not baseline.is_file():
                raise FileNotFoundError(f"baseline file missing in snapshot: {rel}")
            target = source_dir / rel_path
            if target.exists() and not target.is_symlink() and sha256_file(target) == expected_hash:
                continue  # already identical to baseline
            if dry_run:
                result["restored"].append(rel)
                if target.exists():
                    result["backed_up"].append(rel)
                continue
            if target.exists():
                result["backed_up"].append(str(self._backup_target(target, source_dir, "before_rollback")))
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(baseline, target)
            result["restored"].append(rel)

        # Files created after the snapshot are moved aside, never deleted.
        for rel in sorted(set(current.keys()) - set(record.get("files", {}).keys())):
            target = source_dir / safe_rel(rel)
            if not target.exists():
                continue
            if dry_run:
                result["removed_from_source"].append(rel)
                continue
            result["removed_from_source"].append(str(self._backup_target(target, source_dir, "after_snapshot")))

        return result

    # ----------------------------------------------------------------- export
    def export(self, source_dir: Path, record: Dict[str, Any], bundle_name: str = "") -> Dict[str, Any]:
        """Export current versions of changed files as a reusable bundle."""
        source_dir = Path(source_dir).resolve()
        changes = self.diff(source_dir, record)
        name = bundle_name or f"bundle_{source_dir.name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        content_dir = self.snapshots_dir / name / "files"
        current = collect_files(source_dir)

        hashes: Dict[str, str] = {}
        for rel in changes["added"] + changes["modified"]:
            dest = content_dir / safe_rel(rel)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(current[rel], dest)
            hashes[rel] = sha256_file(current[rel])

        bundle = {
            "schema": PATCH_SCHEMA,
            "id": name,
            "kind": "bundle",
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "base_snapshot": record.get("id", ""),
            "description": record.get("description", ""),
            "content_dir": f"snapshots/{name}/files",
            "file_count": len(hashes),
            "files": hashes,
            "author": AUTHOR,
        }
        self._write_record(self.patches_dir / f"patch_{name}.json", bundle)
        return bundle

    # ------------------------------------------------------------------ apply
    def apply(self, source_dir: Path, bundle: Dict[str, Any],
              dry_run: bool = False) -> Dict[str, Any]:
        source_dir = Path(source_dir).resolve()
        content_dir = self._has_content(bundle)
        result: Dict[str, Any] = {"applied": [], "backed_up": [], "dry_run": dry_run}

        for rel in bundle.get("files", {}):
            rel_path = safe_rel(rel)
            src = content_dir / rel_path
            if not src.is_file():
                raise FileNotFoundError(f"bundle file missing: {rel}")
            target = source_dir / rel_path
            if target.exists() and not target.is_symlink() and sha256_file(target) == sha256_file(src):
                continue
            if dry_run:
                result["applied"].append(rel)
                if target.exists():
                    result["backed_up"].append(rel)
                continue
            if target.exists():
                result["backed_up"].append(str(self._backup_target(target, source_dir, "before_apply")))
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
            result["applied"].append(rel)

        return result
