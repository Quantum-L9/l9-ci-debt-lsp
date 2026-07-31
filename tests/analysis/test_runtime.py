from __future__ import annotations

import pytest

from l9_debt_lsp.analysis.models import PackContext
from l9_debt_lsp.analysis.runtime import (
    IncrementalAnalysisRuntime,
)
from tests.fixtures.analysis.fake_sdk import (
    FakeAnalysisSession,
)


@pytest.mark.asyncio
async def test_complete_analysis_preserves_version_and_pack() -> None:
    runtime = IncrementalAnalysisRuntime(FakeAnalysisSession())
    pack = PackContext(
        pack_id="pack_" + "a" * 64,
        pack_version="1.0.0",
        corpus_snapshot="cs_" + "b" * 64,
        compiler_version="1.0.0",
        taxonomy_version="1.0.0",
        sdk_contract_version="l9.integration-contract/v1",
    )
    workspace = await runtime.open_workspace(
        workspace_uri="file:///workspace",
        pack=pack,
    )
    document = await runtime.open_document(
        workspace_id=workspace["workspace_id"],
        uri="file:///workspace/a.py",
        language_id="python",
        version=1,
        text="print('hello')",
    )
    result = await runtime.evaluate_document(
        workspace_id=workspace["workspace_id"],
        document_id=document["document_id"],
    )
    assert result["status"] == "complete"
    assert result["document_version"] == 1
    assert result["active_pack_id"] == pack.pack_id
    assert len(result["findings"]) == 1


@pytest.mark.asyncio
async def test_incomplete_sdk_result_is_not_pass() -> None:
    runtime = IncrementalAnalysisRuntime(FakeAnalysisSession(complete=False))
    pack = PackContext(
        pack_id="pack_" + "a" * 64,
        pack_version="1.0.0",
        corpus_snapshot="cs_" + "b" * 64,
        compiler_version="1.0.0",
        taxonomy_version="1.0.0",
        sdk_contract_version="l9.integration-contract/v1",
    )
    workspace = await runtime.open_workspace(
        workspace_uri="file:///workspace",
        pack=pack,
    )
    document = await runtime.open_document(
        workspace_id=workspace["workspace_id"],
        uri="file:///workspace/a.py",
        language_id="python",
        version=1,
        text="incomplete",
    )
    result = await runtime.evaluate_document(
        workspace_id=workspace["workspace_id"],
        document_id=document["document_id"],
    )
    assert result["status"] == "incomplete"
    assert result["limitations"]
