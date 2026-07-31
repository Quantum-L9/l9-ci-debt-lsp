from __future__ import annotations

from pathlib import Path

import pytest

from l9_debt_lsp.actions.builder import CodeActionBuilder
from l9_debt_lsp.actions.errors import CodeActionSuppressed
from tests.fixtures.actions.template import (
    valid_diagnostic,
    valid_template,
)

ROOT = Path(__file__).resolve().parents[2]


def test_incomplete_analysis_has_no_fix() -> None:
    document_id = "doc_" + "d" * 64
    pack_id = "pack_" + "e" * 64
    diagnostic = valid_diagnostic(
        document_id=document_id,
        document_version=1,
        pack_id=pack_id,
        pack_version="1.0.0",
    )
    diagnostic["data"]["analysis_status"] = "incomplete"
    builder = CodeActionBuilder(ROOT / "schemas/lsp")
    with pytest.raises(CodeActionSuppressed):
        builder.build(
            diagnostic=diagnostic,
            templates=[valid_template()],
            document_uri="file:///workspace/example.py",
            workspace_uri="file:///workspace",
            document_id=document_id,
            document_version=1,
            document_text="wrong\n",
            active_pack_id=pack_id,
            active_pack_version="1.0.0",
            corpus_snapshot="cs_" + "b" * 64,
        )
