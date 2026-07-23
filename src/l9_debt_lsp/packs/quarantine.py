from __future__ import annotations

from pathlib import Path
from typing import Any

from .hashing import namespaced_hash, sha256_bytes, sha256_file
from .jsonio import write_canonical_json
from .time import format_utc, utc_now


class QuarantineStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def record(
        self,
        *,
        reason_code: str,
        reason: str,
        manifest_path: Path | None,
        archive_path: Path | None,
        limitations: list[str] | None = None,
    ) -> dict[str, Any]:
        manifest_hash = (
            sha256_file(manifest_path)
            if manifest_path is not None and manifest_path.is_file()
            else None
        )
        archive_hash = (
            sha256_file(archive_path)
            if archive_path is not None and archive_path.is_file()
            else None
        )
        identity = {
            "archive_sha256": archive_hash,
            "manifest_sha256": manifest_hash,
            "reason_code": reason_code,
        }
        quarantine_id = namespaced_hash(
            "quarantine_",
            identity,
        )
        destination = self.root / quarantine_id
        destination.mkdir(parents=True, exist_ok=True)
        destination.chmod(0o700)
        record = {
            "schema_version": "l9.pack-quarantine-record/v1",
            "quarantine_id": quarantine_id,
            "reason_code": reason_code,
            "reason": reason,
            "archive_sha256": archive_hash,
            "manifest_sha256": manifest_hash,
            "observed_at": format_utc(utc_now()),
            "limitations": sorted(set(limitations or [])),
        }
        write_canonical_json(
            destination / "rejection.json",
            record,
        )
        if manifest_path is not None and manifest_path.is_file():
            manifest_bytes = manifest_path.read_bytes()
            write_canonical_json(
                destination / "publication-manifest-reference.json",
                {
                    "schema_version": ("l9.quarantined-manifest-reference/v1"),
                    "sha256": sha256_bytes(manifest_bytes),
                    "size": len(manifest_bytes),
                    "source_name": manifest_path.name,
                },
            )
        if archive_path is not None and archive_path.is_file():
            write_canonical_json(
                destination / "archive-reference.json",
                {
                    "schema_version": ("l9.quarantined-archive-reference/v1"),
                    "sha256": archive_hash,
                    "size": archive_path.stat().st_size,
                    "source_name": archive_path.name,
                },
            )
        return record
