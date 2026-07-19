from __future__ import annotations

import asyncio
from collections.abc import Iterable

from l9_debt_lsp.packs.time import format_utc, utc_now

from .errors import (
    DocumentLimitError,
    DocumentNotFoundError,
    DocumentVersionError,
    WorkspaceClosedError,
    WorkspaceNotFoundError,
)
from .identity import document_identity, workspace_identity
from .models import (
    DocumentOverlay,
    PackContext,
    WorkspaceSessionState,
)
from .sdk_protocol import AnalysisSession

MAX_DOCUMENT_BYTES = 5 * 1024 * 1024
MAX_OPEN_DOCUMENTS = 5000
MAX_OVERLAY_BYTES = 256 * 1024 * 1024
MAX_DEPENDENCY_EDGES = 100_000
MAX_INVALIDATION_DOCUMENTS = 250


class WorkspaceManager:
    def __init__(self, sdk: AnalysisSession) -> None:
        self._sdk = sdk
        self._workspaces: dict[
            str,
            WorkspaceSessionState,
        ] = {}
        self._lock = asyncio.Lock()

    async def open_workspace(
        self,
        *,
        workspace_uri: str,
        pack: PackContext,
    ) -> WorkspaceSessionState:
        workspace_id = workspace_identity(workspace_uri)
        async with self._lock:
            existing = self._workspaces.get(workspace_id)
            if existing is not None and existing.state == "open":
                if (
                    existing.active_pack is not None
                    and existing.active_pack.pack_id != pack.pack_id
                ):
                    existing.generation += 1
                    existing.active_pack = pack
                    existing.limitations.add(
                        "Active pack changed; previous analyses are stale."
                    )
                return existing
            state = WorkspaceSessionState(
                workspace_id=workspace_id,
                generation=0,
                state="created",
                active_pack=pack,
            )
            self._workspaces[workspace_id] = state
        await self._sdk.open_workspace(
            workspace_id=workspace_id,
            pack=pack,
        )
        async with self._lock:
            state.state = "open"
            return state

    async def close_workspace(
        self,
        workspace_id: str,
    ) -> None:
        async with self._lock:
            state = self._require_workspace(workspace_id)
            if state.state == "closed":
                return
            state.state = "closing"
            state.generation += 1
            document_ids = tuple(state.documents)
        for document_id in document_ids:
            await self._sdk.close_document(
                workspace_id=workspace_id,
                document_id=document_id,
            )
        await self._sdk.close_workspace(
            workspace_id=workspace_id,
        )
        async with self._lock:
            state.documents.clear()
            state.reverse_dependencies.clear()
            state.state = "closed"

    async def open_document(
        self,
        *,
        workspace_id: str,
        uri: str,
        language_id: str,
        version: int,
        text: str,
    ) -> DocumentOverlay:
        self._validate_document_content(text)
        document_id = document_identity(uri)
        now = format_utc(utc_now())
        async with self._lock:
            state = self._require_open_workspace(workspace_id)
            existing = state.documents.get(document_id)
            if existing is not None and existing.state == "open":
                raise DocumentVersionError(f"document is already open: {document_id}")
            if (
                sum(document.state == "open" for document in state.documents.values())
                >= MAX_OPEN_DOCUMENTS
            ):
                raise DocumentLimitError("workspace open-document limit exceeded")
            overlay = DocumentOverlay(
                document_id=document_id,
                uri=uri,
                language_id=language_id,
                version=version,
                text=text,
                opened_at=now,
                updated_at=now,
            )
            projected_bytes = state.overlay_bytes + overlay.content_bytes
            if projected_bytes > MAX_OVERLAY_BYTES:
                raise DocumentLimitError("workspace overlay byte limit exceeded")
            state.documents[document_id] = overlay
            state.generation += 1
        try:
            await self._sdk.open_document(
                workspace_id=workspace_id,
                document_id=document_id,
                uri=uri,
                language_id=language_id,
                version=version,
                text=text,
            )
        except Exception:
            async with self._lock:
                state.documents.pop(document_id, None)
                state.generation += 1
            raise
        return overlay

    async def update_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        version: int,
        text: str,
    ) -> DocumentOverlay:
        self._validate_document_content(text)
        async with self._lock:
            state = self._require_open_workspace(workspace_id)
            overlay = self._require_document(
                state,
                document_id,
            )
            if version <= overlay.version:
                raise DocumentVersionError(
                    "document versions must be strictly increasing"
                )
            previous_text = overlay.text
            previous_version = overlay.version
            previous_updated_at = overlay.updated_at
            projected_bytes = (
                state.overlay_bytes - overlay.content_bytes + len(text.encode("utf-8"))
            )
            if projected_bytes > MAX_OVERLAY_BYTES:
                raise DocumentLimitError("workspace overlay byte limit exceeded")
            overlay.text = text
            overlay.version = version
            overlay.updated_at = format_utc(utc_now())
            state.generation += 1
        try:
            await self._sdk.update_document(
                workspace_id=workspace_id,
                document_id=document_id,
                version=version,
                text=text,
            )
        except Exception:
            async with self._lock:
                overlay.text = previous_text
                overlay.version = previous_version
                overlay.updated_at = previous_updated_at
                state.generation += 1
            raise
        return overlay

    async def close_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> None:
        async with self._lock:
            state = self._require_open_workspace(workspace_id)
            overlay = self._require_document(
                state,
                document_id,
            )
            overlay.state = "closed"
            overlay.text = ""
            overlay.updated_at = format_utc(utc_now())
            state.generation += 1
            state.reverse_dependencies.pop(
                document_id,
                None,
            )
            for dependents in state.reverse_dependencies.values():
                dependents.discard(document_id)
        await self._sdk.close_document(
            workspace_id=workspace_id,
            document_id=document_id,
        )

    async def update_dependencies(
        self,
        *,
        workspace_id: str,
        document_id: str,
        dependencies: Iterable[str],
    ) -> tuple[str, ...]:
        normalized = tuple(sorted(set(dependencies)))
        async with self._lock:
            state = self._require_open_workspace(workspace_id)
            self._require_document(state, document_id)
            for dependents in state.reverse_dependencies.values():
                dependents.discard(document_id)
            for dependency in normalized:
                state.reverse_dependencies.setdefault(
                    dependency,
                    set(),
                ).add(document_id)
            if state.dependency_edge_count > MAX_DEPENDENCY_EDGES:
                state.limitations.add("Dependency graph limit exceeded.")
                raise DocumentLimitError("dependency edge limit exceeded")
            state.generation += 1
        return normalized

    async def invalidated_dependents(
        self,
        *,
        workspace_id: str,
        changed_document_id: str,
    ) -> tuple[str, ...]:
        async with self._lock:
            state = self._require_open_workspace(workspace_id)
            dependents = sorted(
                state.reverse_dependencies.get(
                    changed_document_id,
                    set(),
                )
            )
            if len(dependents) > MAX_INVALIDATION_DOCUMENTS:
                state.limitations.add(
                    "Dependency invalidation exceeded the bounded limit."
                )
                dependents = dependents[:MAX_INVALIDATION_DOCUMENTS]
            result = tuple(dependents)
        if result:
            await self._sdk.invalidate_dependencies(
                workspace_id=workspace_id,
                document_ids=result,
            )
        return result

    async def snapshot(
        self,
        workspace_id: str,
    ) -> WorkspaceSessionState:
        async with self._lock:
            return self._require_workspace(workspace_id)

    def get_workspace_nowait(
        self,
        workspace_id: str,
    ) -> WorkspaceSessionState:
        return self._require_workspace(workspace_id)

    @staticmethod
    def _validate_document_content(text: str) -> None:
        size = len(text.encode("utf-8"))
        if size > MAX_DOCUMENT_BYTES:
            raise DocumentLimitError(f"document exceeds {MAX_DOCUMENT_BYTES} bytes")

    def _require_workspace(
        self,
        workspace_id: str,
    ) -> WorkspaceSessionState:
        state = self._workspaces.get(workspace_id)
        if state is None:
            raise WorkspaceNotFoundError(workspace_id)
        return state

    def _require_open_workspace(
        self,
        workspace_id: str,
    ) -> WorkspaceSessionState:
        state = self._require_workspace(workspace_id)
        if state.state != "open":
            raise WorkspaceClosedError(workspace_id)
        return state

    @staticmethod
    def _require_document(
        state: WorkspaceSessionState,
        document_id: str,
    ) -> DocumentOverlay:
        overlay = state.documents.get(document_id)
        if overlay is None or overlay.state != "open":
            raise DocumentNotFoundError(document_id)
        return overlay
