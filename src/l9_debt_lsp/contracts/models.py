from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PackDescriptor:
    pack_id: str
    pack_version: str
    protocol: str
    corpus_snapshot: str
    analysis_run: str
    compilation_id: str
    compiler_version: str
    taxonomy_version: str
    sdk_contract_version: str
    runtime_rule_kinds: tuple[str, ...]
    limitations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.lsp-pack-descriptor/v1",
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "protocol": self.protocol,
            "corpus_snapshot": self.corpus_snapshot,
            "analysis_run": self.analysis_run,
            "compilation_id": self.compilation_id,
            "compiler_version": self.compiler_version,
            "taxonomy_version": self.taxonomy_version,
            "sdk_contract_version": self.sdk_contract_version,
            "runtime_rule_kinds": list(self.runtime_rule_kinds),
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class CompatibilityResult:
    status: str
    pack_id: str
    pack_version: str
    checks: dict[str, bool]
    limitations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.lsp-pack-compatibility-result/v1",
            "status": self.status,
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "checks": dict(sorted(self.checks.items())),
            "limitations": list(self.limitations),
        }
