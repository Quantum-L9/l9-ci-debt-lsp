from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PackContext:
    pack_id: str
    pack_version: str
    corpus_snapshot: str
    compiler_version: str
    taxonomy_version: str
    sdk_contract_version: str


@dataclass
class DocumentOverlay:
    document_id: str
    uri: str
    language_id: str
    version: int
    text: str
    opened_at: str
    updated_at: str
    state: str = "open"

    @property
    def content_bytes(self) -> int:
        return len(self.text.encode("utf-8"))

    def metadata(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.document-overlay/v1",
            "document_id": self.document_id,
            "uri": self.uri,
            "language_id": self.language_id,
            "version": self.version,
            "content_bytes": self.content_bytes,
            "state": self.state,
            "opened_at": self.opened_at,
            "updated_at": self.updated_at,
        }


@dataclass
class WorkspaceSessionState:
    workspace_id: str
    generation: int
    state: str
    active_pack: PackContext | None
    documents: dict[str, DocumentOverlay] = field(default_factory=dict)
    reverse_dependencies: dict[str, set[str]] = field(default_factory=dict)
    limitations: set[str] = field(default_factory=set)

    @property
    def overlay_bytes(self) -> int:
        return sum(
            document.content_bytes
            for document in self.documents.values()
            if document.state == "open"
        )

    @property
    def dependency_edge_count(self) -> int:
        return sum(len(dependents) for dependents in self.reverse_dependencies.values())

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.workspace-state/v1",
            "workspace_id": self.workspace_id,
            "generation": self.generation,
            "state": self.state,
            "open_document_count": sum(
                document.state == "open" for document in self.documents.values()
            ),
            "overlay_bytes": self.overlay_bytes,
            "dependency_edge_count": (self.dependency_edge_count),
            "active_pack_id": (
                self.active_pack.pack_id if self.active_pack is not None else None
            ),
            "limitations": sorted(self.limitations),
        }


@dataclass(frozen=True)
class AnalysisRequest:
    request_id: str
    workspace_id: str
    workspace_generation: int
    document_id: str
    document_uri: str
    document_version: int
    language_id: str
    active_pack_id: str
    active_pack_version: str
    created_at: str
    limitations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.analysis-request/v1",
            "request_id": self.request_id,
            "workspace_id": self.workspace_id,
            "workspace_generation": self.workspace_generation,
            "document_id": self.document_id,
            "document_uri": self.document_uri,
            "document_version": self.document_version,
            "language_id": self.language_id,
            "active_pack_id": self.active_pack_id,
            "active_pack_version": self.active_pack_version,
            "created_at": self.created_at,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class SDKAnalysisResult:
    findings: tuple[dict[str, Any], ...]
    limitations: tuple[str, ...]
    complete: bool
    dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class AnalysisResult:
    request_id: str
    workspace_id: str
    workspace_generation: int
    document_id: str
    document_version: int
    active_pack_id: str
    status: str
    findings: tuple[dict[str, Any], ...]
    limitations: tuple[str, ...]
    latency_ms: float
    latency_class: str
    completed_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.analysis-result/v1",
            "request_id": self.request_id,
            "workspace_id": self.workspace_id,
            "workspace_generation": self.workspace_generation,
            "document_id": self.document_id,
            "document_version": self.document_version,
            "active_pack_id": self.active_pack_id,
            "status": self.status,
            "findings": list(self.findings),
            "limitations": list(self.limitations),
            "latency_ms": round(self.latency_ms, 3),
            "latency_class": self.latency_class,
            "completed_at": self.completed_at,
        }
