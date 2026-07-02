"""Tests for code_actions.py — verifies quick fixes produce correct WorkspaceEdits."""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

from lsprotocol.types import (
    CodeActionContext,
    CodeActionParams,
    Diagnostic,
    DiagnosticSeverity,
    Position,
    Range,
    TextDocumentIdentifier,
)
from rules_loader import BUILTIN_RULES
from code_actions import compute_code_actions


def _make_diagnostic(rule_id: str) -> Diagnostic:
    return Diagnostic(
        range=Range(start=Position(line=0, character=0), end=Position(line=0, character=10)),
        message=f"{rule_id} violation",
        severity=DiagnosticSeverity.Error,
        source="l9-ci-debt-lsp",
        code=rule_id,
    )


def _make_params(uri: str, rule_id: str) -> CodeActionParams:
    return CodeActionParams(
        text_document=TextDocumentIdentifier(uri=uri),
        range=Range(start=Position(line=0, character=0), end=Position(line=1, character=0)),
        context=CodeActionContext(diagnostics=[_make_diagnostic(rule_id)]),
    )


def test_ci_import_001_quick_fix_produces_edit() -> None:
    yaml_text = "jobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n"
    params = _make_params("file:///workspace/.github/workflows/ci.yml", "CI-IMPORT-001")
    actions = compute_code_actions(yaml_text, params, BUILTIN_RULES)
    assert len(actions) >= 1
    fix_actions = [a for a in actions if a.edit is not None]
    assert len(fix_actions) >= 1, "Expected at least one action with a WorkspaceEdit"
    action = fix_actions[0]
    uri = "file:///workspace/.github/workflows/ci.yml"
    assert uri in action.edit.changes  # type: ignore[union-attr]
    edits = action.edit.changes[uri]  # type: ignore[index]
    assert any("PYTHONPATH" in e.new_text for e in edits)


def test_ci_deps_001_quick_fix_produces_edit() -> None:
    toml_text = "[build-system]\nrequires = [\"hatchling\"]\n\n[project]\nname = \"foo\"\n"
    params = _make_params("file:///workspace/pyproject.toml", "CI-DEPS-001")
    actions = compute_code_actions(toml_text, params, BUILTIN_RULES)
    fix_actions = [a for a in actions if a.edit is not None]
    assert len(fix_actions) >= 1
    uri = "file:///workspace/pyproject.toml"
    edits = fix_actions[0].edit.changes[uri]  # type: ignore[index,union-attr]
    assert any("dependencies" in e.new_text for e in edits)


def test_doctrine_has_no_workspace_edit() -> None:
    """Doctrine violations must never have an auto-apply WorkspaceEdit."""
    python_text = "from transport import PacketEnvelope\n"
    params = _make_params("file:///workspace/transport/sender.py", "DOCTRINE")
    actions = compute_code_actions(python_text, params, BUILTIN_RULES)
    edit_actions = [a for a in actions if a.edit is not None]
    assert len(edit_actions) == 0, (
        "DOCTRINE violation produced an auto-apply WorkspaceEdit — this is not allowed."
    )
    # Should still have a 'open docs' action
    doc_actions = [a for a in actions if a.command is not None]
    assert len(doc_actions) >= 1
