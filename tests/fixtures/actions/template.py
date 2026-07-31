from __future__ import annotations

from typing import Any


def valid_template(
    *,
    canonical_rule_id: str = "l9.example.rule",
    replacement: str = "fixed",
) -> dict[str, Any]:
    return {
        "schema_version": "l9.quick-fix-template/v1",
        "template_id": "fix_" + "a" * 64,
        "canonical_rule_id": canonical_rule_id,
        "title": "Apply deterministic fix",
        "kind": "deterministic_template",
        "safety": "deterministic",
        "scope": "current_document",
        "edits": [
            {
                "start_line": 0,
                "start_character": 0,
                "end_line": 0,
                "end_character": 5,
                "replacement": replacement,
            }
        ],
        "limitations": [],
    }


def valid_diagnostic(
    *,
    document_id: str,
    document_version: int,
    pack_id: str,
    pack_version: str,
) -> dict[str, Any]:
    return {
        "range": {
            "start": {"line": 0, "character": 0},
            "end": {"line": 0, "character": 5},
        },
        "severity": 2,
        "code": "l9.example.rule",
        "source": "l9-ci-debt",
        "message": "Example",
        "tags": [],
        "related_information": [],
        "data": {
            "schema_version": "l9.diagnostic-data/v1",
            "finding_id": "finding-1",
            "canonical_rule_id": "l9.example.rule",
            "provider_rule_id": "provider.example",
            "document_identity": document_id,
            "document_version": document_version,
            "rule_pack_id": pack_id,
            "rule_pack_version": pack_version,
            "corpus_snapshot": "cs_" + "b" * 64,
            "analysis_request_id": "request_" + "c" * 64,
            "analysis_status": "complete",
            "limitations": [],
        },
    }
