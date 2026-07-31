from __future__ import annotations

from pathlib import Path
from typing import Any

from l9_debt_lsp.packs.hashing import namespaced_hash

from .errors import DiagnosticError
from .limitations import limitation_diagnostic
from .models import (
    CanonicalDiagnostic,
    DiagnosticPublication,
)
from .ordering import deduplicate_and_order
from .projection import project_finding
from .validation import FindingValidator

MAX_DIAGNOSTICS_PER_DOCUMENT = 200


class DiagnosticBuilder:
    def __init__(self, schema_root: Path) -> None:
        self._validator = FindingValidator(
            schema_root / "sdk-finding-consumer.schema.json"
        )

    def build(
        self,
        *,
        analysis_result: dict[str, Any],
        document_uri: str,
        document_text: str,
        rule_pack_version: str,
        corpus_snapshot: str,
    ) -> DiagnosticPublication:
        status = str(analysis_result["status"])
        if status not in {
            "complete",
            "incomplete",
            "failed",
        }:
            raise DiagnosticError(f"analysis status cannot be published: {status}")
        findings = analysis_result.get("findings", [])
        if not isinstance(findings, list):
            raise DiagnosticError("analysis findings must be an array")
        analysis_limitations = tuple(
            sorted(
                set(
                    str(value)
                    for value in analysis_result.get(
                        "limitations",
                        [],
                    )
                )
            )
        )
        projected: list[CanonicalDiagnostic] = []
        projection_limitations: set[str] = set()
        for finding in findings:
            if not isinstance(finding, dict):
                projection_limitations.add("An SDK finding was not an object.")
                continue
            try:
                projected.append(
                    project_finding(
                        finding=finding,
                        validator=self._validator,
                        document_id=analysis_result["document_id"],
                        document_uri=document_uri,
                        document_version=analysis_result["document_version"],
                        document_text=document_text,
                        rule_pack_id=analysis_result["active_pack_id"],
                        rule_pack_version=rule_pack_version,
                        corpus_snapshot=corpus_snapshot,
                        analysis_request_id=analysis_result["request_id"],
                        analysis_status=(
                            "complete" if status == "complete" else "incomplete"
                        ),
                        analysis_limitations=analysis_limitations,
                    )
                )
            except Exception as error:
                projection_limitations.add(
                    "A finding was suppressed because it could not be "
                    f"represented safely: {type(error).__name__}."
                )
        ordered, duplicate_limitations = deduplicate_and_order(projected)
        limitations = set(analysis_limitations)
        limitations.update(projection_limitations)
        limitations.update(duplicate_limitations)
        diagnostic_values = list(ordered)
        if len(diagnostic_values) > MAX_DIAGNOSTICS_PER_DOCUMENT:
            omitted = len(diagnostic_values) - MAX_DIAGNOSTICS_PER_DOCUMENT
            diagnostic_values = diagnostic_values[:MAX_DIAGNOSTICS_PER_DOCUMENT]
            limitations.add(
                f"{omitted} diagnostics were omitted because the "
                "per-document limit was exceeded."
            )
        if status != "complete" or limitations:
            diagnostic_values.append(
                limitation_diagnostic(
                    document_id=analysis_result["document_id"],
                    document_version=analysis_result["document_version"],
                    rule_pack_id=analysis_result["active_pack_id"],
                    rule_pack_version=rule_pack_version,
                    corpus_snapshot=corpus_snapshot,
                    analysis_request_id=analysis_result["request_id"],
                    limitations=tuple(sorted(limitations))
                    or ("Analysis did not complete.",),
                )
            )
        final_diagnostics, final_duplicate_limitations = deduplicate_and_order(
            diagnostic_values
        )
        limitations.update(final_duplicate_limitations)
        publication_identity = {
            "workspace_id": analysis_result["workspace_id"],
            "workspace_generation": analysis_result["workspace_generation"],
            "document_id": analysis_result["document_id"],
            "document_version": analysis_result["document_version"],
            "rule_pack_id": analysis_result["active_pack_id"],
            "rule_pack_version": rule_pack_version,
            "analysis_request_id": analysis_result["request_id"],
            "diagnostic_identities": [
                {
                    "finding_id": diagnostic.data["finding_id"],
                    "canonical_rule_id": diagnostic.data["canonical_rule_id"],
                    "range": diagnostic.range.as_dict(),
                }
                for diagnostic in final_diagnostics
            ],
        }
        return DiagnosticPublication(
            publication_id=namespaced_hash(
                "publication_",
                publication_identity,
            ),
            workspace_id=analysis_result["workspace_id"],
            workspace_generation=analysis_result["workspace_generation"],
            document_id=analysis_result["document_id"],
            document_uri=document_uri,
            document_version=analysis_result["document_version"],
            rule_pack_id=analysis_result["active_pack_id"],
            rule_pack_version=rule_pack_version,
            analysis_request_id=analysis_result["request_id"],
            analysis_status=status,
            diagnostics=final_diagnostics,
            limitations=tuple(sorted(limitations)),
        )
