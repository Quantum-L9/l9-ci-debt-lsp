from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TrustedKey:
    key_id: str
    algorithm: str
    public_key: str
    enabled: bool
    usages: tuple[str, ...]
    issuer: str
    not_before: str | None
    not_after: str | None
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class InstalledPack:
    pack_id: str
    pack_version: str
    path: Path
    archive_sha256: str
    manifest_sha256: str
    signer_key_id: str
    corpus_snapshot: str
    compiler_version: str
    taxonomy_version: str
    sdk_contract_version: str
    limitations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.pack-installation-result/v1",
            "status": "installed",
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "path": self.path.as_posix(),
            "archive_sha256": self.archive_sha256,
            "manifest_sha256": self.manifest_sha256,
            "signer_key_id": self.signer_key_id,
            "corpus_snapshot": self.corpus_snapshot,
            "compiler_version": self.compiler_version,
            "taxonomy_version": self.taxonomy_version,
            "sdk_contract_version": self.sdk_contract_version,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class ActivationPointer:
    pack_id: str
    pack_version: str
    archive_sha256: str
    corpus_snapshot: str
    compiler_version: str
    taxonomy_version: str
    sdk_contract_version: str
    activated_at: str
    activation_id: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.pack-activation-pointer/v1",
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "archive_sha256": self.archive_sha256,
            "corpus_snapshot": self.corpus_snapshot,
            "compiler_version": self.compiler_version,
            "taxonomy_version": self.taxonomy_version,
            "sdk_contract_version": self.sdk_contract_version,
            "activated_at": self.activated_at,
            "activation_id": self.activation_id,
        }
