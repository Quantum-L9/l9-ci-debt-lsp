from __future__ import annotations

from typing import Any

from lsprotocol.types import (
    Diagnostic,
    DiagnosticRelatedInformation,
    DiagnosticSeverity,
    DiagnosticTag,
    Location,
    Position,
    Range,
)


def to_lsp_diagnostic(
    value: dict[str, Any],
) -> Diagnostic:
    diagnostic_range = value["range"]
    related = [
        DiagnosticRelatedInformation(
            location=Location(
                uri=item["location"]["uri"],
                range=Range(
                    start=Position(
                        line=item["location"]["range"]["start"]["line"],
                        character=item["location"]["range"]["start"]["character"],
                    ),
                    end=Position(
                        line=item["location"]["range"]["end"]["line"],
                        character=item["location"]["range"]["end"]["character"],
                    ),
                ),
            ),
            message=item["message"],
        )
        for item in value["related_information"]
    ]
    tags = [DiagnosticTag(tag) for tag in value["tags"]]
    return Diagnostic(
        range=Range(
            start=Position(
                line=diagnostic_range["start"]["line"],
                character=diagnostic_range["start"]["character"],
            ),
            end=Position(
                line=diagnostic_range["end"]["line"],
                character=diagnostic_range["end"]["character"],
            ),
        ),
        message=value["message"],
        severity=DiagnosticSeverity(value["severity"]),
        code=value["code"],
        source=value["source"],
        tags=tags or None,
        related_information=related or None,
        data=value["data"],
    )
