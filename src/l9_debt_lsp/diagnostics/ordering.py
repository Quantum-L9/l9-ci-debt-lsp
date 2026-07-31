from __future__ import annotations

from .models import CanonicalDiagnostic
from .severity import SEVERITY_RANK


def diagnostic_sort_key(
    diagnostic: CanonicalDiagnostic,
) -> tuple[object, ...]:
    return (
        diagnostic.range.start.line,
        diagnostic.range.start.character,
        diagnostic.range.end.line,
        diagnostic.range.end.character,
        SEVERITY_RANK.get(diagnostic.severity, 99),
        diagnostic.data["canonical_rule_id"],
        diagnostic.data["finding_id"],
    )


def diagnostic_identity(
    diagnostic: CanonicalDiagnostic,
) -> tuple[object, ...]:
    return (
        diagnostic.data["finding_id"],
        diagnostic.data["canonical_rule_id"],
        diagnostic.data["document_identity"],
        diagnostic.range.start.line,
        diagnostic.range.start.character,
        diagnostic.range.end.line,
        diagnostic.range.end.character,
        diagnostic.data["rule_pack_id"],
    )


def deduplicate_and_order(
    diagnostics: list[CanonicalDiagnostic],
) -> tuple[
    tuple[CanonicalDiagnostic, ...],
    tuple[str, ...],
]:
    ordered = sorted(
        diagnostics,
        key=diagnostic_sort_key,
    )
    unique: dict[
        tuple[object, ...],
        CanonicalDiagnostic,
    ] = {}
    limitations: set[str] = set()
    for diagnostic in ordered:
        identity = diagnostic_identity(diagnostic)
        existing = unique.get(identity)
        if existing is None:
            unique[identity] = diagnostic
            continue
        if existing.as_dict() != diagnostic.as_dict():
            limitations.add(
                "Conflicting duplicate diagnostic representation "
                f"for finding {diagnostic.data['finding_id']}."
            )
    return (
        tuple(
            sorted(
                unique.values(),
                key=diagnostic_sort_key,
            )
        ),
        tuple(sorted(limitations)),
    )
