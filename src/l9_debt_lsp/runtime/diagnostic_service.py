from __future__ import annotations

from pathlib import Path

from l9_debt_lsp.analysis.runtime import (
    IncrementalAnalysisRuntime,
)
from l9_debt_lsp.diagnostics.builder import DiagnosticBuilder
from l9_debt_lsp.diagnostics.models import DiagnosticPublication
from l9_debt_lsp.diagnostics.publisher import DiagnosticPublisher


class DiagnosticService:
    def __init__(
        self,
        *,
        runtime: IncrementalAnalysisRuntime,
        publisher: DiagnosticPublisher,
        schema_root: Path,
    ) -> None:
        self.runtime = runtime
        self.publisher = publisher
        self.builder = DiagnosticBuilder(schema_root)

    async def evaluate_and_publish(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> DiagnosticPublication | None:
        workspace = self.runtime.workspaces.get_workspace_nowait(workspace_id)
        overlay = workspace.documents.get(document_id)
        if overlay is None or overlay.state != "open":
            return None
        if workspace.active_pack is None:
            return None
        analysis = await self.runtime.evaluate_document(
            workspace_id=workspace_id,
            document_id=document_id,
        )
        if analysis["status"] in {
            "cancelled",
            "stale",
        }:
            return None
        publication = self.builder.build(
            analysis_result=analysis,
            document_uri=overlay.uri,
            document_text=overlay.text,
            rule_pack_version=(workspace.active_pack.pack_version),
            corpus_snapshot=(workspace.active_pack.corpus_snapshot),
        )
        published = await self.publisher.publish(publication)
        return publication if published else None

    async def close_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        document_uri: str,
    ) -> None:
        await self.publisher.clear(
            workspace_id=workspace_id,
            document_id=document_id,
            document_uri=document_uri,
        )
        await self.runtime.close_document(
            workspace_id=workspace_id,
            document_id=document_id,
        )
