from __future__ import annotations

from typing import Any

from lsprotocol.types import (
    CodeAction,
    CodeActionKind,
    Position,
    Range,
    TextEdit,
    WorkspaceEdit,
)


def to_lsp_code_action(
    value: dict[str, Any],
) -> CodeAction:
    changes: dict[str, list[TextEdit]] = {}
    for uri, edits in value["edit"]["changes"].items():
        changes[uri] = [
            TextEdit(
                range=Range(
                    start=Position(
                        line=edit["range"]["start"]["line"],
                        character=edit["range"]["start"]["character"],
                    ),
                    end=Position(
                        line=edit["range"]["end"]["line"],
                        character=edit["range"]["end"]["character"],
                    ),
                ),
                new_text=edit["newText"],
            )
            for edit in edits
        ]
    return CodeAction(
        title=value["title"],
        kind=CodeActionKind.QuickFix,
        is_preferred=value["is_preferred"],
        edit=WorkspaceEdit(changes=changes),
        data={
            "schema_version": "l9.code-action-data/v1",
            "preview": value["preview"],
            "provenance": value["provenance"],
            "requires_explicit_user_approval": True,
        },
    )
