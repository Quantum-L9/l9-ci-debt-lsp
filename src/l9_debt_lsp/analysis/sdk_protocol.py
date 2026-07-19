from __future__ import annotations

from typing import Protocol, runtime_checkable

from .cancellation import CancellationToken
from .models import PackContext, SDKAnalysisResult


@runtime_checkable
class AnalysisSession(Protocol):
    """Public SDK incremental-analysis contract."""

    async def open_workspace(
        self,
        *,
        workspace_id: str,
        pack: PackContext,
    ) -> None:
        """Open a workspace analysis session."""

    async def close_workspace(
        self,
        *,
        workspace_id: str,
    ) -> None:
        """Close and release a workspace analysis session."""

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
        """Open a document overlay."""

    async def update_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        version: int,
        text: str,
    ) -> None:
        """Replace a document overlay with a newer version."""

    async def evaluate_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        version: int,
        pack: PackContext,
        cancellation: CancellationToken,
    ) -> SDKAnalysisResult:
        """Evaluate one exact document version."""

    async def close_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> None:
        """Close and release a document overlay."""

    async def invalidate_dependencies(
        self,
        *,
        workspace_id: str,
        document_ids: tuple[str, ...],
    ) -> None:
        """Invalidate a bounded set of dependent documents."""
