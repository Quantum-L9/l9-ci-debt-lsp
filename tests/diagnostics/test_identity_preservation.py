from __future__ import annotations

from pathlib import Path

from l9_debt_lsp.diagnostics.builder import DiagnosticBuilder
from tests.fixtures.diagnostics.finding import valid_finding

ROOT = Path(__file__).resolve().parents[2]


def test_canonical_identity_is_preserved_exactly() -> None:
    document_id = "doc_" + "a" * 64
    uri = "file:///workspace/example.py"
    finding = valid_finding(
        document_id=document_id,
        uri=uri,
        finding_id="sdk-finding-identity",
        canonical_rule_id="l9.canonical.identity",
    )
    builder = DiagnosticBuilder(ROOT / "schemas/lsp")
    publication = builder.build(
        analysis_result={
            "request_id": "request_" + "b" * 64,
            "workspace_id": "workspace_" + "c" * 64,
            "workspace_generation": 1,
            "document_id": document_id,
            "document_version": 7,
            "active_pack_id": "pack_" + "d" * 64,
            "status": "complete",
            "findings": [finding],
            "limitations": [],
        },
        document_uri=uri,
        document_text="hello\n",
        rule_pack_version="1.2.3",
        corpus_snapshot="cs_" + "e" * 64,
    )
    diagnostic = publication.diagnostics[0]
    assert diagnostic.data["finding_id"] == ("sdk-finding-identity")
    assert diagnostic.data["canonical_rule_id"] == ("l9.canonical.identity")
    assert diagnostic.data["provider_rule_id"] == ("provider.example")
    assert diagnostic.data["document_identity"] == document_id
    assert diagnostic.data["document_version"] == 7
    assert diagnostic.data["rule_pack_version"] == "1.2.3"
    assert diagnostic.data["corpus_snapshot"] == ("cs_" + "e" * 64)
