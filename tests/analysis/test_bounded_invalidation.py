from __future__ import annotations

import pytest

from l9_debt_lsp.analysis.models import PackContext
from l9_debt_lsp.analysis.workspace import WorkspaceManager
from tests.fixtures.analysis.fake_sdk import (
    FakeAnalysisSession,
)


@pytest.mark.asyncio
async def test_dependency_invalidation_is_deterministic() -> None:
    sdk = FakeAnalysisSession()
    manager = WorkspaceManager(sdk)
    pack = PackContext(
        pack_id="pack_" + "a" * 64,
        pack_version="1.0.0",
        corpus_snapshot="cs_" + "b" * 64,
        compiler_version="1.0.0",
        taxonomy_version="1.0.0",
        sdk_contract_version="l9.integration-contract/v1",
    )
    state = await manager.open_workspace(
        workspace_uri="file:///workspace",
        pack=pack,
    )
    source = await manager.open_document(
        workspace_id=state.workspace_id,
        uri="file:///workspace/source.py",
        language_id="python",
        version=1,
        text="source",
    )
    dependent = await manager.open_document(
        workspace_id=state.workspace_id,
        uri="file:///workspace/dependent.py",
        language_id="python",
        version=1,
        text="dependent",
    )
    await manager.update_dependencies(
        workspace_id=state.workspace_id,
        document_id=dependent.document_id,
        dependencies=(source.document_id,),
    )
    invalidated = await manager.invalidated_dependents(
        workspace_id=state.workspace_id,
        changed_document_id=source.document_id,
    )
    assert invalidated == (dependent.document_id,)
