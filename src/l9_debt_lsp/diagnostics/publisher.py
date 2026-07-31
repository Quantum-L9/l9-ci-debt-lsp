from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from l9_debt_lsp.analysis.workspace import WorkspaceManager

from .errors import DiagnosticPublicationError
from .models import DiagnosticPublication

PublishCallback = Callable[
    [str, list[dict[str, object]]],
    Awaitable[None],
]


@dataclass(frozen=True)
class PublicationState:
    publication_id: str
    document_version: int
    rule_pack_id: str
    diagnostic_count: int


class DiagnosticPublisher:
    def __init__(
        self,
        *,
        workspaces: WorkspaceManager,
        callback: PublishCallback,
    ) -> None:
        self._workspaces = workspaces
        self._callback = callback
        self._published: dict[
            tuple[str, str],
            PublicationState,
        ] = {}
        self._locks: dict[
            tuple[str, str],
            asyncio.Lock,
        ] = {}

    async def publish(
        self,
        publication: DiagnosticPublication,
    ) -> bool:
        key = (
            publication.workspace_id,
            publication.document_id,
        )
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            state = self._workspaces.get_workspace_nowait(publication.workspace_id)
            if state.state != "open":
                return False
            overlay = state.documents.get(publication.document_id)
            if overlay is None or overlay.state != "open":
                return False
            if overlay.version != publication.document_version:
                return False
            if state.generation != publication.workspace_generation:
                return False
            if (
                state.active_pack is None
                or state.active_pack.pack_id != publication.rule_pack_id
            ):
                return False
            diagnostics = [value.as_dict() for value in publication.diagnostics]
            try:
                await self._callback(
                    publication.document_uri,
                    diagnostics,
                )
            except Exception as error:
                raise DiagnosticPublicationError(
                    f"diagnostic callback failed: {error}"
                ) from error
            self._published[key] = PublicationState(
                publication_id=publication.publication_id,
                document_version=publication.document_version,
                rule_pack_id=publication.rule_pack_id,
                diagnostic_count=len(diagnostics),
            )
            return True

    async def clear(
        self,
        *,
        workspace_id: str,
        document_id: str,
        document_uri: str,
    ) -> None:
        key = (workspace_id, document_id)
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            await self._callback(document_uri, [])
            self._published.pop(key, None)
            self._locks.pop(key, None)

    def state(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> PublicationState | None:
        return self._published.get((workspace_id, document_id))
