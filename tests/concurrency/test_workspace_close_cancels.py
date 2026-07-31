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
async def test_workspace_close_cancels_running_analysis() -> None:
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
        text="content",
    )
    evaluation = asyncio.create_task(
        runtime.evaluate_document(
            workspace_id=workspace["workspace_id"],
            document_id=document["document_id"],
        )
    )
    await asyncio.sleep(0.01)
    await runtime.close_workspace(workspace["workspace_id"])
    result = await evaluation
    assert result["status"] in {
        "cancelled",
        "stale",
    }
