from __future__ import annotations

import json
from pathlib import Path

from lsprotocol.types import (
    CodeActionContext,
    CodeActionParams,
    Diagnostic,
    Position,
    Range,
    TextDocumentIdentifier,
)

from server.code_actions import compute_code_actions
from server.diagnostics import compute_diagnostics

ROOT = Path(__file__).resolve().parents[1]


def _rules() -> list[dict]:
    return json.loads((ROOT / "rules" / "compiled_rules.json").read_text())["rules"]


def _params(uri: str, diagnostics: list[Diagnostic]) -> CodeActionParams:
    return CodeActionParams(
        text_document=TextDocumentIdentifier(uri=uri),
        range=Range(start=Position(line=0, character=0), end=Position(line=0, character=0)),
        context=CodeActionContext(diagnostics=diagnostics),
    )


def test_pythonpath_rule_offers_quick_fix() -> None:
    uri = "file:///tmp/bad-workflow.yml"
    text = (ROOT / "fixtures" / "bad-workflow.yml").read_text()
    diagnostics = compute_diagnostics(text, uri, _rules())
    actions = compute_code_actions(text, _params(uri, diagnostics), _rules())
    titles = [action.title for action in actions]
    assert any("PYTHONPATH" in title for title in titles)
    assert any(action.edit for action in actions)


def test_doctrine_rule_offers_docs_action_not_edit() -> None:
    uri = "file:///tmp/doctrine-violation.py"
    text = (ROOT / "fixtures" / "doctrine-violation.py").read_text()
    diagnostics = compute_diagnostics(text, uri, _rules())
    actions = compute_code_actions(text, _params(uri, diagnostics), _rules())
    doctrine_actions = [action for action in actions if "DOCTRINE" in action.title]
    assert doctrine_actions
    assert all(action.edit is None for action in doctrine_actions)
