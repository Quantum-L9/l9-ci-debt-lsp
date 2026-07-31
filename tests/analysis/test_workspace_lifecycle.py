from __future__ import annotations

import pytest

from l9_debt_lsp.analysis.errors import (
    DocumentVersionError,
)
from l9_debt_lsp.analysis.models import PackContext
from l9_debt_lsp.analysis.workspace import WorkspaceManager
from tests.fixtures.analysis.fake_sdk import (
    FakeAnalysisSession,
)


@pytest.mark.asyncio
async def test_document_versions_are_strictly_increasing() -> None:
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
    uri = "file:///workspace/a.py"
    overlay = await manager.open_document(
        workspace_id=state.workspace_id,
        uri=uri,
        language_id="python",
        version=1,
        text="print('a')",
    )
    with pytest.raises(DocumentVersionError):
        await manager.update_document(
            workspace_id=state.workspace_id,
            document_id=overlay.document_id,
            version=1,
            text="print('b')",
        )
    updated = await manager.update_document(
        workspace_id=state.workspace_id,
        document_id=overlay.document_id,
        version=2,
        text="print('b')",
    )
    assert updated.version == 2
