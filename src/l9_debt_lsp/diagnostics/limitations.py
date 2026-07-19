from __future__ import annotations

from .models import (
    CanonicalDiagnostic,
    Position,
    Range,
)


def limitation_diagnostic(
    *,
    document_id: str,
    document_version: int,
    rule_pack_id: str,
    rule_pack_version: str,
    corpus_snapshot: str,
    analysis_request_id: str,
    limitations: tuple[str, ...],
    finding_id: str = "l9-analysis-incomplete",
) -> CanonicalDiagnostic:
    message = ("L9 analysis is incomplete. " + " ".join(limitations[:5])).strip()
    if len(message) > 2000:
        message = message[:1999] + "…"
    return CanonicalDiagnostic(
        range=Range(
            start=Position(0, 0),
            end=Position(0, 0),
        ),
        severity=2,
        code="l9.analysis.incomplete",
        source="l9-ci-debt",
        message=message,
        tags=(),
        related_information=(),
        data={
            "schema_version": "l9.diagnostic-data/v1",
            "finding_id": finding_id,
            "canonical_rule_id": "l9.analysis.incomplete",
            "provider_rule_id": "l9-lsp-runtime",
            "document_identity": document_id,
            "document_version": document_version,
            "rule_pack_id": rule_pack_id,
            "rule_pack_version": rule_pack_version,
            "corpus_snapshot": corpus_snapshot,
            "analysis_request_id": analysis_request_id,
            "analysis_status": "incomplete",
            "limitations": list(limitations),
        },
    )
