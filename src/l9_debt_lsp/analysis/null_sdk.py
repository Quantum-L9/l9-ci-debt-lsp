from __future__ import annotations

from .cancellation import CancellationToken
from .models import PackContext, SDKAnalysisResult


class UnavailableAnalysisSession:
    """Fail-closed adapter used until a real SDK binding is configured."""

    async def open_workspace(
        self,
        *,
        workspace_id: str,
        pack: PackContext,
    ) -> None:
        del workspace_id, pack

    async def close_workspace(
        self,
        *,
        workspace_id: str,
    ) -> None:
        del workspace_id

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
        del (
            workspace_id,
            document_id,
            uri,
            language_id,
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
        del workspace_id, document_id, version, text

    async def evaluate_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        version: int,
        pack: PackContext,
        cancellation: CancellationToken,
    ) -> SDKAnalysisResult:
        del workspace_id, document_id, version, pack
        cancellation.raise_if_cancelled()
        return SDKAnalysisResult(
            findings=(),
            limitations=(
                "SDK AnalysisSession adapter is unavailable.",
                "No complete analysis was performed.",
            ),
            complete=False,
            dependencies=(),
        )

    async def close_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> None:
        del workspace_id, document_id

    async def invalidate_dependencies(
        self,
        *,
        workspace_id: str,
        document_ids: tuple[str, ...],
    ) -> None:
        del workspace_id, document_ids
