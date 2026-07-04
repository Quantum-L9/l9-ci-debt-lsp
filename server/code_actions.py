"""Compute LSP CodeActions (quick fixes) for L9 CI-debt diagnostics."""
from __future__ import annotations

import re
from typing import Any

from lsprotocol.types import (
    CodeAction,
    CodeActionKind,
    CodeActionParams,
    Position,
    Range,
    TextEdit,
    WorkspaceEdit,
)


def compute_code_actions(
    text: str,
    params: CodeActionParams,
    rules: list[dict[str, Any]],
) -> list[CodeAction]:
    actions: list[CodeAction] = []
    uri = params.text_document.uri

    # Only offer fixes for diagnostics that overlap the cursor range
    relevant_rule_ids = {
        d.code for d in (params.context.diagnostics or []) if d.code
    }
    if not relevant_rule_ids:
        return actions

    for rule in rules:
        rule_id = rule.get("id")
        if rule_id not in relevant_rule_ids:
            continue
        quick_fix = rule.get("quick_fix")
        if not quick_fix:
            # Doctrine violations and multi-line structural changes have no
            # auto-fix — open the docs instead.
            actions.append(
                CodeAction(
                    title=f"L9: Open docs for {rule_id}",
                    kind=CodeActionKind.QuickFix,
                    command={
                        "title": "Open finding documentation",
                        "command": "l9CiDebt.openFindingDocs",
                        "arguments": [rule_id],
                    },
                )
            )
            continue

        insert_pattern = quick_fix.get("insert_after_pattern", "")
        insert_text = quick_fix.get("insert_text", "")
        label = quick_fix.get("label", f"Fix {rule_id}")

        if not insert_pattern or not insert_text:
            continue

        match = re.search(insert_pattern, text, re.MULTILINE)
        if not match:
            continue

        insert_line = text[: match.end()].count("\n")
        edit_range = Range(
            start=Position(line=insert_line + 1, character=0),
            end=Position(line=insert_line + 1, character=0),
        )

        workspace_edit = WorkspaceEdit(
            changes={uri: [TextEdit(range=edit_range, new_text=insert_text)]}
        )

        actions.append(
            CodeAction(
                title=f"L9: {label}",
                kind=CodeActionKind.QuickFix,
                edit=workspace_edit,
                diagnostics=[
                    d
                    for d in (params.context.diagnostics or [])
                    if d.code == rule_id
                ],
                is_preferred=True,
            )
        )

    return actions
