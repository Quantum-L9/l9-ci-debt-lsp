from __future__ import annotations

from typing import Any

from .errors import FindingValidationError, SourceLocationError
from .location import (
    clamp_primary_range,
    source_location_from_dict,
)
from .models import (
    CanonicalDiagnostic,
    RelatedInformation,
)
from .sanitization import sanitize_message
from .severity import diagnostic_severity, diagnostic_tags
from .validation import FindingValidator

MAX_RELATED_INFORMATION = 20


def related_information(
    finding: dict[str, Any],
) -> tuple[RelatedInformation, ...]:
    projected: list[RelatedInformation] = []
    evidence = finding.get("evidence", [])
    if isinstance(evidence, list):
        for item in evidence:
            if not isinstance(item, dict):
                continue
            location_value = item.get("source_location")
            if not isinstance(location_value, dict):
                continue
            try:
                location = source_location_from_dict(location_value)
            except SourceLocationError:
                continue
            kind = str(item.get("kind", "evidence"))
            summary = sanitize_message(
                str(item.get("summary", "Related evidence")),
                maximum=1000,
            )
            projected.append(
                RelatedInformation(
                    uri=location.uri,
                    range=location.range,
                    message=f"{kind}: {summary}",
                )
            )
    explicit = finding.get("related_locations", [])
    if isinstance(explicit, list):
        for item in explicit:
            if not isinstance(item, dict):
                continue
            location_value = item.get("source_location")
            if not isinstance(location_value, dict):
                continue
            try:
                location = source_location_from_dict(location_value)
            except SourceLocationError:
                continue
            projected.append(
                RelatedInformation(
                    uri=location.uri,
                    range=location.range,
                    message=sanitize_message(
                        str(item.get("message", "Related location")),
                        maximum=1000,
                    ),
                )
            )
    unique: dict[
        tuple[str, int, int, int, int, str],
        RelatedInformation,
    ] = {}
    for item in projected:
        key = (
            item.uri,
            item.range.start.line,
            item.range.start.character,
            item.range.end.line,
            item.range.end.character,
            item.message,
        )
        unique.setdefault(key, item)
    ordered = sorted(
        unique.values(),
        key=lambda item: (
            item.uri,
            item.range.start.line,
            item.range.start.character,
            item.range.end.line,
            item.range.end.character,
            item.message,
        ),
    )
    return tuple(ordered[:MAX_RELATED_INFORMATION])


def project_finding(
    *,
    finding: dict[str, Any],
    validator: FindingValidator,
    document_id: str,
    document_uri: str,
    document_version: int,
    document_text: str,
    rule_pack_id: str,
    rule_pack_version: str,
    corpus_snapshot: str,
    analysis_request_id: str,
    analysis_status: str,
    analysis_limitations: tuple[str, ...],
) -> CanonicalDiagnostic:
    validator.validate(finding)
    location_value = finding["source_location"]
    if not isinstance(location_value, dict):
        raise FindingValidationError("finding source_location must be an object")
    location = source_location_from_dict(location_value)
    if location.document_identity != document_id:
        raise SourceLocationError(
            "primary finding document identity does not match the evaluated document"
        )
    if location.uri != document_uri:
        raise SourceLocationError(
            "primary finding URI does not match evaluated document"
        )
    source_range = clamp_primary_range(
        location,
        document_text=document_text,
    )
    finding_limitations = finding.get("limitations", [])
    if not isinstance(finding_limitations, list):
        finding_limitations = []
    limitations = tuple(
        sorted(
            set(
                str(item) for item in (list(analysis_limitations) + finding_limitations)
            )
        )
    )
    return CanonicalDiagnostic(
        range=source_range,
        severity=diagnostic_severity(str(finding["severity"])),
        code=str(finding["canonical_rule_id"]),
        source="l9-ci-debt",
        message=sanitize_message(str(finding["message"])),
        tags=diagnostic_tags(finding.get("tags")),
        related_information=related_information(finding),
        data={
            "schema_version": "l9.diagnostic-data/v1",
            "finding_id": str(finding["finding_id"]),
            "canonical_rule_id": str(finding["canonical_rule_id"]),
            "provider_rule_id": str(finding["provider_rule_id"]),
            "document_identity": document_id,
            "document_version": document_version,
            "rule_pack_id": rule_pack_id,
            "rule_pack_version": rule_pack_version,
            "corpus_snapshot": corpus_snapshot,
            "analysis_request_id": analysis_request_id,
            "analysis_status": analysis_status,
            "limitations": list(limitations),
        },
    )
