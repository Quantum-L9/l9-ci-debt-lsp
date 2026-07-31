from __future__ import annotations

from l9_debt_lsp.actions.models import (
    Position,
    RemediationTemplate,
    TextEdit,
)
from l9_debt_lsp.actions.preview import build_preview


def test_preview_contains_bounded_unified_diff() -> None:
    template = RemediationTemplate(
        template_id="fix_" + "a" * 64,
        canonical_rule_id="l9.example",
        title="Replace value",
        kind="deterministic_template",
        safety="deterministic",
        scope="current_document",
        edits=(
            TextEdit(
                start=Position(0, 0),
                end=Position(0, 3),
                replacement="new",
            ),
        ),
        limitations=(),
    )
    summary, diff, limitations = build_preview(
        relative_path="src/example.py",
        text="old\n",
        template=template,
    )
    assert "Replace value" in summary
    assert "-old" in diff
    assert "+new" in diff
    assert limitations == ()
