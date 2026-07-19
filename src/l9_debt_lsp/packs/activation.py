from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from l9_debt_lsp.contracts.schema import SchemaValidator
from .errors import ActivationError, RollbackError
from .hashing import namespaced_hash
from .jsonio import (
    append_canonical_jsonl,
    load_json,
    write_canonical_json,
)
from .models import ActivationPointer, InstalledPack
from .paths import StatePaths
from .retirement import RetirementRegistry
from .store import PackStore
from .time import format_utc, utc_now
class ActivationManager:
    def __init__(
        self,
        *,
        paths: StatePaths,
        schema_root: Path,
    ) -> None:
        self.paths = paths
        self.store = PackStore(
            packs_root=paths.packs,
            staging_root=paths.staging,
        )
        self.retirement = RetirementRegistry(
            paths.retired_packs,
            schema_root / "retired-pack-registry.schema.json",
        )
        self.pointer_validator = SchemaValidator(
            schema_root / "activation-pointer.schema.json"
        )
    def load_active(self) -> ActivationPointer | None:
        return self._load_pointer(self.paths.active)
    def load_previous(self) -> ActivationPointer | None:
        return self._load_pointer(self.paths.previous)
    def activate(
        self,
        pack_id: str,
        *,
        operation: str = "activate",
    ) -> ActivationPointer:
        self.paths.initialize()
        target = self.store.verify_integrity(pack_id)
        self.retirement.require_not_retired(
            pack_id=target.pack_id,
            pack_version=target.pack_version,
        )
        current = self.load_active()
        occurred_at = format_utc(utc_now())
        activation_id = namespaced_hash(
            "activation_",
            {
                "operation": operation,
                "target_pack_id": target.pack_id,
                "previous_pack_id": (
                    current.pack_id
                    if current is not None
                    else None
                ),
                "target_archive_sha256": (
                    target.archive_sha256
                ),
                "occurred_at": occurred_at,
            },
        )
        pointer = self._pointer_from_pack(
            target,
            activated_at=occurred_at,
            activation_id=activation_id,
        )
        try:
            if current is not None and current.pack_id != target.pack_id:
                write_canonical_json(
                    self.paths.previous,
                    current.as_dict(),
                )
            write_canonical_json(
                self.paths.active,
                pointer.as_dict(),
            )
            self._append_history(
                operation=operation,
                activation_id=activation_id,
                target_pack_id=target.pack_id,
                previous_pack_id=(
                    current.pack_id
                    if current is not None
                    else None
                ),
                occurred_at=occurred_at,
                status="succeeded",
                limitations=[],
            )
            return pointer
        except Exception as error:
            self._append_history(
                operation=operation,
                activation_id=activation_id,
                target_pack_id=target.pack_id,
                previous_pack_id=(
                    current.pack_id
                    if current is not None
                    else None
                ),
                occurred_at=occurred_at,
                status="failed",
                limitations=[str(error)],
            )
            raise ActivationError(
                f"atomic pack activation failed: {error}"
            ) from error
    def rollback(self) -> ActivationPointer:
        previous = self.load_previous()
        if previous is None:
            raise RollbackError(
                "no previous-known-good pack is available"
            )
        try:
            return self.activate(
                previous.pack_id,
                operation="rollback",
            )
        except Exception as error:
            raise RollbackError(
                f"rollback failed: {error}"
            ) from error
    def recover(self) -> dict[str, Any]:
        self.paths.initialize()
        active = self.load_active()
        previous = self.load_previous()
        result: dict[str, Any] = {
            "schema_version": "l9.activation-recovery/v1",
            "status": "valid",
            "active_pack_id": None,
            "previous_pack_id": None,
            "limitations": [],
        }
        if active is not None:
            try:
                installed = self.store.verify_integrity(
                    active.pack_id
                )
                self.retirement.require_not_retired(
                    pack_id=installed.pack_id,
                    pack_version=installed.pack_version,
                )
                result["active_pack_id"] = active.pack_id
            except Exception as error:
                result["status"] = "degraded"
                result["limitations"].append(
                    f"active pack invalid: {error}"
                )
        if previous is not None:
            try:
                installed = self.store.verify_integrity(
                    previous.pack_id
                )
                self.retirement.require_not_retired(
                    pack_id=installed.pack_id,
                    pack_version=installed.pack_version,
                )
                result["previous_pack_id"] = previous.pack_id
            except Exception as error:
                result["status"] = "degraded"
                result["limitations"].append(
                    f"previous-known-good invalid: {error}"
                )
        return result
    def _load_pointer(
        self,
        path: Path,
    ) -> ActivationPointer | None:
        if not path.is_file():
            return None
        document = load_json(path)
        self.pointer_validator.validate(document)
        return ActivationPointer(
            pack_id=document["pack_id"],
            pack_version=document["pack_version"],
            archive_sha256=document["archive_sha256"],
            corpus_snapshot=document["corpus_snapshot"],
            compiler_version=document["compiler_version"],
            taxonomy_version=document["taxonomy_version"],
            sdk_contract_version=document[
                "sdk_contract_version"
            ],
            activated_at=document["activated_at"],
            activation_id=document["activation_id"],
        )
    @staticmethod
    def _pointer_from_pack(
        pack: InstalledPack,
        *,
        activated_at: str,
        activation_id: str,
    ) -> ActivationPointer:
        return ActivationPointer(
            pack_id=pack.pack_id,
            pack_version=pack.pack_version,
            archive_sha256=pack.archive_sha256,
            corpus_snapshot=pack.corpus_snapshot,
            compiler_version=pack.compiler_version,
            taxonomy_version=pack.taxonomy_version,
            sdk_contract_version=pack.sdk_contract_version,
            activated_at=activated_at,
            activation_id=activation_id,
        )
    def _append_history(
        self,
        *,
        operation: str,
        activation_id: str,
        target_pack_id: str,
        previous_pack_id: str | None,
        occurred_at: str,
        status: str,
        limitations: list[str],
    ) -> None:
        sequence = 1
        if self.paths.activation_history.is_file():
            with self.paths.activation_history.open(
                "r",
                encoding="utf-8",
            ) as stream:
                sequence += sum(
                    1 for line in stream if line.strip()
                )
        append_canonical_jsonl(
            self.paths.activation_history,
            {
                "schema_version": (
                    "l9.pack-activation-history-entry/v1"
                ),
                "sequence": sequence,
                "operation": operation,
                "activation_id": activation_id,
                "target_pack_id": target_pack_id,
                "previous_pack_id": previous_pack_id,
                "occurred_at": occurred_at,
                "status": status,
                "limitations": sorted(set(limitations)),
            },
        )
