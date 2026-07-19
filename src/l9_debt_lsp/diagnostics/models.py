from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, order=True)
class Position:
    line: int
    character: int

    def as_dict(self) -> dict[str, int]:
        return {
            "line": self.line,
            "character": self.character,
        }


@dataclass(frozen=True)
class Range:
    start: Position
    end: Position

    def as_dict(self) -> dict[str, Any]:
        return {
            "start": self.start.as_dict(),
            "end": self.end.as_dict(),
        }


@dataclass(frozen=True)
class SourceLocation:
    document_identity: str
    uri: str
    range: Range


@dataclass(frozen=True)
class RelatedInformation:
    uri: str
    range: Range
    message: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "location": {
                "uri": self.uri,
                "range": self.range.as_dict(),
            },
            "message": self.message,
        }


@dataclass(frozen=True)
class CanonicalDiagnostic:
    range: Range
    severity: int
    code: str
    source: str
    message: str
    tags: tuple[int, ...]
    related_information: tuple[RelatedInformation, ...]
    data: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.canonical-diagnostic/v1",
            "range": self.range.as_dict(),
            "severity": self.severity,
            "code": self.code,
            "source": self.source,
            "message": self.message,
            "tags": list(self.tags),
            "related_information": [
                value.as_dict() for value in self.related_information
            ],
            "data": self.data,
        }


@dataclass(frozen=True)
class DiagnosticPublication:
    publication_id: str
    workspace_id: str
    workspace_generation: int
    document_id: str
    document_uri: str
    document_version: int
    rule_pack_id: str
    rule_pack_version: str
    analysis_request_id: str
    analysis_status: str
    diagnostics: tuple[CanonicalDiagnostic, ...]
    limitations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.diagnostic-publication/v1",
            "publication_id": self.publication_id,
            "workspace_id": self.workspace_id,
            "workspace_generation": self.workspace_generation,
            "document_id": self.document_id,
            "document_uri": self.document_uri,
            "document_version": self.document_version,
            "rule_pack_id": self.rule_pack_id,
            "rule_pack_version": self.rule_pack_version,
            "analysis_request_id": self.analysis_request_id,
            "analysis_status": self.analysis_status,
            "diagnostic_count": len(self.diagnostics),
            "diagnostics": [diagnostic.as_dict() for diagnostic in self.diagnostics],
            "limitations": list(self.limitations),
        }
