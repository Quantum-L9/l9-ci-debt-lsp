from __future__ import annotations

import asyncio

from l9_debt_lsp.analysis.cancellation import (
    CancellationToken,
)
from l9_debt_lsp.analysis.models import (
    PackContext,
    SDKAnalysisResult,
)


class FakeAnalysisSession:
    def __init__(
        self,
        *,
        delay: float = 0.0,
        complete: bool = True,
    ) -> None:
        self.delay = delay
        self.complete = complete
        self.workspaces: set[str] = set()
        self.documents: dict[
            tuple[str, str],
            tuple[int, str],
        ] = {}

    async def open_workspace(
        self,
        *,
        workspace_id: str,
        pack: PackContext,
    ) -> None:
        del pack
        self.workspaces.add(workspace_id)

    async def close_workspace(
        self,
        *,
        workspace_id: str,
    ) -> None:
        self.workspaces.discard(workspace_id)

    async def open_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        uri: str,
        language_id: str,
        version: int,
        text: str,
    ) -> None:
        del uri, language_id
        self.documents[(workspace_id, document_id)] = (
            version,
            text,
        )

    async def update_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        version: int,
        text: str,
    ) -> None:
        self.documents[(workspace_id, document_id)] = (
            version,
            text,
        )

    async def evaluate_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        version: int,
        pack: PackContext,
        cancellation: CancellationToken,
    ) -> SDKAnalysisResult:
        del pack
        if self.delay:
            await asyncio.sleep(self.delay)
        cancellation.raise_if_cancelled()
        stored_version, text = self.documents[(workspace_id, document_id)]
        assert stored_version == version
        return SDKAnalysisResult(
            findings=(
                {
                    "finding_id": (f"finding-{document_id}-{version}"),
                    "canonical_rule_id": "l9.example",
                    "message": text,
                },
            ),
            limitations=(() if self.complete else ("partial parse",)),
            complete=self.complete,
            dependencies=(),
        )

    async def close_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> None:
        self.documents.pop(
            (workspace_id, document_id),
            None,
        )

    async def invalidate_dependencies(
        self,
        *,
        workspace_id: str,
        document_ids: tuple[str, ...],
    ) -> None:
        del workspace_id, document_ids
