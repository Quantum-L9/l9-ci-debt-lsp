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
class TextEdit:
    start: Position
    end: Position
    replacement: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "range": {
                "start": self.start.as_dict(),
                "end": self.end.as_dict(),
            },
            "newText": self.replacement,
        }


@dataclass(frozen=True)
class RemediationTemplate:
    template_id: str
    canonical_rule_id: str
    title: str
    kind: str
    safety: str
    scope: str
    edits: tuple[TextEdit, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class CodeActionProvenance:
    action_id: str
    template_id: str
    finding_id: str
    canonical_rule_id: str
    provider_rule_id: str
    document_identity: str
    document_version: int
    rule_pack_id: str
    rule_pack_version: str
    corpus_snapshot: str
    analysis_request_id: str
    edit_digest: str
    limitations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.code-action-provenance/v1",
            "action_id": self.action_id,
            "template_id": self.template_id,
            "finding_id": self.finding_id,
            "canonical_rule_id": self.canonical_rule_id,
            "provider_rule_id": self.provider_rule_id,
            "document_identity": self.document_identity,
            "document_version": self.document_version,
            "rule_pack_id": self.rule_pack_id,
            "rule_pack_version": self.rule_pack_version,
            "corpus_snapshot": self.corpus_snapshot,
            "analysis_request_id": self.analysis_request_id,
            "edit_digest": self.edit_digest,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class BoundedCodeAction:
    title: str
    document_uri: str
    edits: tuple[TextEdit, ...]
    preview_summary: str
    preview_diff: str
    preview_limitations: tuple[str, ...]
    provenance: CodeActionProvenance
    is_preferred: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.bounded-code-action/v1",
            "title": self.title,
            "kind": "quickfix",
            "is_preferred": self.is_preferred,
            "edit": {
                "changes": {self.document_uri: [edit.as_dict() for edit in self.edits]}
            },
            "preview": {
                "summary": self.preview_summary,
                "diff": self.preview_diff,
                "limitations": list(self.preview_limitations),
            },
            "provenance": self.provenance.as_dict(),
        }
