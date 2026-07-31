from __future__ import annotations

import pytest

from l9_debt_lsp.analysis.models import PackContext
from l9_debt_lsp.analysis.workspace import WorkspaceManager
from l9_debt_lsp.diagnostics.models import (
    CanonicalDiagnostic,
    DiagnosticPublication,
    Position,
    Range,
)
from l9_debt_lsp.diagnostics.publisher import (
    DiagnosticPublisher,
)
from tests.fixtures.analysis.fake_sdk import (
    FakeAnalysisSession,
)


@pytest.mark.asyncio
async def test_old_document_version_is_not_published() -> None:
    sdk = FakeAnalysisSession()
    workspaces = WorkspaceManager(sdk)
    pack = PackContext(
        pack_id="pack_" + "a" * 64,
        pack_version="1.0.0",
        corpus_snapshot="cs_" + "b" * 64,
        compiler_version="1.0.0",
        taxonomy_version="1.0.0",
        sdk_contract_version="l9.integration-contract/v1",
    )
    workspace = await workspaces.open_workspace(
        workspace_uri="file:///workspace",
        pack=pack,
    )
    document = await workspaces.open_document(
        workspace_id=workspace.workspace_id,
        uri="file:///workspace/a.py",
        language_id="python",
        version=2,
        text="content",
    )
    published: list[object] = []

    async def callback(
        uri: str,
        diagnostics: list[dict[str, object]],
    ) -> None:
        published.append((uri, diagnostics))

    publisher = DiagnosticPublisher(
        workspaces=workspaces,
        callback=callback,
    )
    diagnostic = CanonicalDiagnostic(
        range=Range(
            start=Position(0, 0),
            end=Position(0, 1),
        ),
        severity=2,
        code="l9.example",
        source="l9-ci-debt",
        message="Example",
        tags=(),
        related_information=(),
        data={
            "schema_version": "l9.diagnostic-data/v1",
            "finding_id": "finding-1",
            "canonical_rule_id": "l9.example",
            "provider_rule_id": "provider.example",
            "document_identity": document.document_id,
            "document_version": 1,
            "rule_pack_id": pack.pack_id,
            "rule_pack_version": pack.pack_version,
            "corpus_snapshot": pack.corpus_snapshot,
            "analysis_request_id": "request_" + "c" * 64,
            "analysis_status": "complete",
            "limitations": [],
        },
    )
    publication = DiagnosticPublication(
        publication_id="publication_" + "d" * 64,
        workspace_id=workspace.workspace_id,
        workspace_generation=workspace.generation,
        document_id=document.document_id,
        document_uri=document.uri,
        document_version=1,
        rule_pack_id=pack.pack_id,
        rule_pack_version=pack.pack_version,
        analysis_request_id="request_" + "c" * 64,
        analysis_status="complete",
        diagnostics=(diagnostic,),
        limitations=(),
    )
    result = await publisher.publish(publication)
    assert result is False
    assert published == []
