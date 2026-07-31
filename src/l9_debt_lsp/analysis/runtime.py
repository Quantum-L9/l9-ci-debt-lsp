from __future__ import annotations

from typing import Any

from .models import PackContext
from .scheduler import AnalysisScheduler
from .sdk_protocol import AnalysisSession
from .workspace import WorkspaceManager


class IncrementalAnalysisRuntime:
    def __init__(self, sdk: AnalysisSession) -> None:
        self.sdk = sdk
        self.workspaces = WorkspaceManager(sdk)
        self.scheduler = AnalysisScheduler(
            sdk=sdk,
            workspaces=self.workspaces,
        )

    async def open_workspace(
        self,
        *,
        workspace_uri: str,
        pack: PackContext,
    ) -> dict[str, Any]:
        state = await self.workspaces.open_workspace(
            workspace_uri=workspace_uri,
            pack=pack,
        )
        return state.as_dict()

    async def close_workspace(
        self,
        workspace_id: str,
    ) -> None:
        await self.scheduler.cancel_workspace(
            workspace_id=workspace_id,
            reason="workspace_closed",
        )
        await self.workspaces.close_workspace(workspace_id)

    async def open_document(
        self,
        *,
        workspace_id: str,
        uri: str,
        language_id: str,
        version: int,
        text: str,
    ) -> dict[str, Any]:
        overlay = await self.workspaces.open_document(
            workspace_id=workspace_id,
            uri=uri,
            language_id=language_id,
            version=version,
            text=text,
        )
        return overlay.metadata()

    async def update_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        version: int,
        text: str,
    ) -> dict[str, Any]:
        await self.scheduler.cancel_document(
            workspace_id=workspace_id,
            document_id=document_id,
            reason="document_updated",
        )
        overlay = await self.workspaces.update_document(
            workspace_id=workspace_id,
            document_id=document_id,
            version=version,
            text=text,
        )
        await self.workspaces.invalidated_dependents(
            workspace_id=workspace_id,
            changed_document_id=document_id,
        )
        return overlay.metadata()

    async def evaluate_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> dict[str, Any]:
        result = await self.scheduler.evaluate(
            workspace_id=workspace_id,
            document_id=document_id,
        )
        return result.as_dict()

    async def close_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> None:
        await self.scheduler.cancel_document(
            workspace_id=workspace_id,
            document_id=document_id,
            reason="document_closed",
        )
        await self.workspaces.close_document(
            workspace_id=workspace_id,
            document_id=document_id,
        )

    async def shutdown(self) -> None:
        await self.scheduler.shutdown()
