from __future__ import annotations

from pathlib import Path

from l9_debt_lsp.actions.builder import CodeActionBuilder
from tests.fixtures.actions.template import (
    valid_diagnostic,
    valid_template,
)

ROOT = Path(__file__).resolve().parents[2]


def test_builds_single_document_workspace_edit() -> None:
    document_id = "doc_" + "d" * 64
    pack_id = "pack_" + "e" * 64
    builder = CodeActionBuilder(ROOT / "schemas/lsp")
    actions = builder.build(
        diagnostic=valid_diagnostic(
            document_id=document_id,
            document_version=3,
            pack_id=pack_id,
            pack_version="1.0.0",
        ),
        templates=[valid_template()],
        document_uri="file:///workspace/example.py",
        workspace_uri="file:///workspace",
        document_id=document_id,
        document_version=3,
        document_text="wrong\n",
        active_pack_id=pack_id,
        active_pack_version="1.0.0",
        corpus_snapshot="cs_" + "b" * 64,
    )
    assert len(actions) == 1
    action = actions[0].as_dict()
    assert list(action["edit"]["changes"]) == ["file:///workspace/example.py"]
    assert (
        action["edit"]["changes"]["file:///workspace/example.py"][0]["newText"]
        == "fixed"
    )
    assert action["provenance"]["finding_id"] == ("finding-1")
    assert action["provenance"]["document_version"] == 3
