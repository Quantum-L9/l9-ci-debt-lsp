from __future__ import annotations

from typing import Any


def valid_finding(
    *,
    document_id: str,
    uri: str,
    finding_id: str = "finding-1",
    canonical_rule_id: str = "l9.example.rule",
    line: int = 0,
) -> dict[str, Any]:
    return {
        "schema_version": "l9.sdk-finding/v1",
        "finding_id": finding_id,
        "canonical_rule_id": canonical_rule_id,
        "provider_rule_id": "provider.example",
        "message": "Example finding",
        "severity": "warning",
        "source_location": {
            "document_identity": document_id,
            "uri": uri,
            "start_line": line,
            "start_character": 0,
            "end_line": line,
            "end_character": 5,
        },
        "evidence": [
            {
                "kind": "structural",
                "summary": "Related evidence",
                "source_location": {
                    "document_identity": document_id,
                    "uri": uri,
                    "start_line": line,
                    "start_character": 0,
                    "end_line": line,
                    "end_character": 5,
                },
            }
        ],
        "related_locations": [],
        "tags": [],
        "limitations": [],
    }
