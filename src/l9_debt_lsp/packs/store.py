from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .errors import (
    ImmutablePackCollisionError,
    PackValidationError,
)
from .hashing import sha256_file
from .jsonio import (
    fsync_directory,
    load_json,
    write_canonical_json,
)
from .models import InstalledPack
from .time import format_utc, utc_now

REQUIRED_INSTALLED_FILES = (
    "manifest.json",
    "defense-pack.json",
    "compatibility.json",
    "checksums.json",
    "installation.json",
    "archive.sha256",
)


class PackStore:
    def __init__(
        self,
        *,
        packs_root: Path,
        staging_root: Path,
    ) -> None:
        self.packs_root = packs_root
        self.staging_root = staging_root

    def pack_path(self, pack_id: str) -> Path:
        return self.packs_root / pack_id

    def install(
        self,
        *,
        extracted_root: Path,
        manifest: dict[str, Any],
        defense_pack: dict[str, Any],
        manifest_path: Path,
        archive_sha256: str,
        signer_key_id: str,
        content_hashes: dict[str, str],
        limitations: list[str],
    ) -> InstalledPack:
        pack_id = defense_pack["pack_id"]
        destination = self.pack_path(pack_id)
        manifest_sha256 = sha256_file(manifest_path)
        if destination.exists():
            installed = self.load(pack_id)
            if (
                installed.archive_sha256 == archive_sha256
                and installed.manifest_sha256 == manifest_sha256
            ):
                return installed
            raise ImmutablePackCollisionError(f"pack identity collision: {pack_id}")
        self.packs_root.mkdir(parents=True, exist_ok=True)
        self.staging_root.mkdir(parents=True, exist_ok=True)
        temporary = Path(
            tempfile.mkdtemp(
                prefix=f".install-{pack_id}.",
                dir=self.staging_root,
            )
        )
        temporary.chmod(0o700)
        try:
            shutil.copytree(
                extracted_root,
                temporary / "content",
                dirs_exist_ok=False,
            )
            content_root = temporary / "content"
            shutil.copy2(
                manifest_path,
                content_root / "manifest.json",
            )
            installation = {
                "schema_version": "l9.pack-installation-record/v1",
                "pack_id": pack_id,
                "pack_version": defense_pack["version"],
                "archive_sha256": archive_sha256,
                "manifest_sha256": manifest_sha256,
                "signer_key_id": signer_key_id,
                "compatibility_state": "compatible",
                "installed_at": format_utc(utc_now()),
                "content_hashes": dict(sorted(content_hashes.items())),
                "limitations": sorted(set(limitations)),
            }
            write_canonical_json(
                content_root / "installation.json",
                installation,
            )
            archive_hash_path = content_root / "archive.sha256"
            archive_hash_path.write_text(
                archive_sha256 + "\n",
                encoding="ascii",
            )
            archive_hash_path.chmod(0o600)
            self._fsync_tree(content_root)
            os.replace(content_root, destination)
            fsync_directory(self.packs_root)
            return self.load(pack_id)
        finally:
            shutil.rmtree(temporary, ignore_errors=True)

    def load(self, pack_id: str) -> InstalledPack:
        root = self.pack_path(pack_id)
        if not root.is_dir():
            raise PackValidationError(f"pack is not installed: {pack_id}")
        missing = [
            name for name in REQUIRED_INSTALLED_FILES if not (root / name).is_file()
        ]
        if missing:
            raise PackValidationError(f"installed pack is incomplete: {missing}")
        installation = load_json(root / "installation.json")
        defense_pack = load_json(root / "defense-pack.json")
        archive_sha256 = (root / "archive.sha256").read_text(encoding="ascii").strip()
        if installation["pack_id"] != pack_id:
            raise PackValidationError("installation pack ID does not match directory")
        if defense_pack["pack_id"] != pack_id:
            raise PackValidationError("defense pack ID does not match directory")
        if archive_sha256 != installation["archive_sha256"]:
            raise PackValidationError(
                "archive hash file does not match installation record"
            )
        return InstalledPack(
            pack_id=pack_id,
            pack_version=installation["pack_version"],
            path=root,
            archive_sha256=archive_sha256,
            manifest_sha256=installation["manifest_sha256"],
            signer_key_id=installation["signer_key_id"],
            corpus_snapshot=defense_pack["corpus_snapshot"],
            compiler_version=defense_pack["compiler_version"],
            taxonomy_version=defense_pack["taxonomy_version"],
            sdk_contract_version=defense_pack["SDK_contract_version"],
            limitations=tuple(sorted(set(installation["limitations"]))),
        )

    def verify_integrity(
        self,
        pack_id: str,
    ) -> InstalledPack:
        installed = self.load(pack_id)
        installation = load_json(installed.path / "installation.json")
        expected_hashes = installation["content_hashes"]
        for relative_name, expected_hash in expected_hashes.items():
            path = installed.path / relative_name
            if not path.is_file():
                raise PackValidationError(
                    f"installed pack member is missing: {relative_name}"
                )
            actual_hash = sha256_file(path)
            if actual_hash != expected_hash:
                raise PackValidationError(
                    f"installed pack member hash mismatch: {relative_name}"
                )
        return installed

    @staticmethod
    def _fsync_tree(root: Path) -> None:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                descriptor = os.open(path, os.O_RDONLY)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
        directories = sorted(
            (path for path in root.rglob("*") if path.is_dir()),
            key=lambda value: len(value.parts),
            reverse=True,
        )
        for directory in directories:
            fsync_directory(directory)
        fsync_directory(root)
