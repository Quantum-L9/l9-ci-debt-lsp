from __future__ import annotations

import asyncio

import pytest

from l9_debt_lsp.analysis.models import PackContext
from l9_debt_lsp.analysis.runtime import (
    IncrementalAnalysisRuntime,
)
from tests.fixtures.analysis.fake_sdk import (
    FakeAnalysisSession,
)


@pytest.mark.asyncio
async def test_new_document_version_suppresses_old_result() -> None:
    runtime = IncrementalAnalysisRuntime(FakeAnalysisSession(delay=0.05))
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
        text="version one",
    )
    first = asyncio.create_task(
        runtime.evaluate_document(
            workspace_id=workspace["workspace_id"],
            document_id=document["document_id"],
        )
    )
    await asyncio.sleep(0.01)
    await runtime.update_document(
        workspace_id=workspace["workspace_id"],
        document_id=document["document_id"],
        version=2,
        text="version two",
    )
    first_result = await first
    assert first_result["status"] in {
        "cancelled",
        "stale",
    }
    second_result = await runtime.evaluate_document(
        workspace_id=workspace["workspace_id"],
        document_id=document["document_id"],
    )
    assert second_result["status"] == "complete"
    assert second_result["document_version"] == 2
