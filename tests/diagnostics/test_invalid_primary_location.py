from __future__ import annotations

from pathlib import Path

from l9_debt_lsp.diagnostics.builder import DiagnosticBuilder
from tests.fixtures.diagnostics.finding import valid_finding

ROOT = Path(__file__).resolve().parents[2]


def test_mismatched_document_identity_is_suppressed() -> None:
    document_id = "doc_" + "a" * 64
    uri = "file:///workspace/example.py"
    finding = valid_finding(
        document_id="doc_" + "f" * 64,
        uri=uri,
    )
    builder = DiagnosticBuilder(ROOT / "schemas/lsp")
    publication = builder.build(
        analysis_result={
            "request_id": "request_" + "b" * 64,
            "workspace_id": "workspace_" + "c" * 64,
            "workspace_generation": 1,
            "document_id": document_id,
            "document_version": 1,
            "active_pack_id": "pack_" + "d" * 64,
            "status": "complete",
            "findings": [finding],
            "limitations": [],
        },
        document_uri=uri,
        document_text="hello",
        rule_pack_version="1.0.0",
        corpus_snapshot="cs_" + "e" * 64,
    )
    assert len(publication.diagnostics) == 1
    assert publication.diagnostics[0].code == ("l9.analysis.incomplete")
