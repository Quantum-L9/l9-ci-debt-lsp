from __future__ import annotations

from typing import Any

from l9_debt_lsp.analysis.runtime import (
    IncrementalAnalysisRuntime,
)


def runtime_health(
    runtime: IncrementalAnalysisRuntime,
    *,
    active_pack_id: str | None,
) -> dict[str, Any]:
    workspaces = runtime.workspaces._workspaces
    open_documents = sum(
        sum(document.state == "open" for document in workspace.documents.values())
        for workspace in workspaces.values()
        if workspace.state == "open"
    )
    running = len(runtime.scheduler._running)
    limitations: list[str] = []
    if active_pack_id is None:
        limitations.append("No active defense pack is configured.")
    status = "healthy" if not limitations else "degraded"
    return {
        "schema_version": "l9.runtime-health/v1",
        "status": status,
        "workspace_count": sum(
            workspace.state == "open" for workspace in workspaces.values()
        ),
        "open_document_count": open_documents,
        "running_evaluation_count": running,
        "queued_evaluation_count": 0,
        "active_pack_id": active_pack_id,
        "limitations": limitations,
    }
