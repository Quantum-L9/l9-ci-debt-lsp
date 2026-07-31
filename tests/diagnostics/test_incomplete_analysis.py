from __future__ import annotations

from pathlib import Path

from l9_debt_lsp.diagnostics.builder import DiagnosticBuilder

ROOT = Path(__file__).resolve().parents[2]


def test_incomplete_empty_analysis_emits_limitation() -> None:
    builder = DiagnosticBuilder(ROOT / "schemas/lsp")
    publication = builder.build(
        analysis_result={
            "request_id": "request_" + "b" * 64,
            "workspace_id": "workspace_" + "c" * 64,
            "workspace_generation": 1,
            "document_id": "doc_" + "a" * 64,
            "document_version": 1,
            "active_pack_id": "pack_" + "d" * 64,
            "status": "incomplete",
            "findings": [],
            "limitations": ["SDK partial parse"],
        },
        document_uri="file:///workspace/example.py",
        document_text="broken syntax",
        rule_pack_version="1.0.0",
        corpus_snapshot="cs_" + "e" * 64,
    )
    assert len(publication.diagnostics) == 1
    diagnostic = publication.diagnostics[0]
    assert diagnostic.code == "l9.analysis.incomplete"
    assert diagnostic.severity == 2
    assert diagnostic.data["analysis_status"] == "incomplete"
