from __future__ import annotations

from pathlib import Path
from typing import Any

from l9_debt_lsp.actions.builder import CodeActionBuilder
from l9_debt_lsp.actions.errors import CodeActionError
from l9_debt_lsp.actions.registry import RemediationRegistry
from l9_debt_lsp.analysis.runtime import (
    IncrementalAnalysisRuntime,
)


class CodeActionService:
    def __init__(
        self,
        *,
        runtime: IncrementalAnalysisRuntime,
        schema_root: Path,
        packs_root: Path,
    ) -> None:
        self.runtime = runtime
        self.packs_root = packs_root
        self.builder = CodeActionBuilder(schema_root)
        self.registry = RemediationRegistry()

    def actions_for_diagnostic(
        self,
        *,
        workspace_id: str,
        workspace_uri: str,
        document_id: str,
        diagnostic: dict[str, Any],
    ) -> list[dict[str, Any]]:
        workspace = self.runtime.workspaces.get_workspace_nowait(workspace_id)
        overlay = workspace.documents.get(document_id)
        if overlay is None or overlay.state != "open" or workspace.active_pack is None:
            return []
        data = diagnostic.get("data")
        if not isinstance(data, dict):
            return []
        canonical_rule_id = data.get("canonical_rule_id")
        if not isinstance(canonical_rule_id, str):
            return []
        pack_root = self.packs_root / workspace.active_pack.pack_id
        templates = self.registry.templates_for_rule(
            pack_root=pack_root,
            canonical_rule_id=canonical_rule_id,
        )
        try:
            actions = self.builder.build(
                diagnostic=diagnostic,
                templates=templates,
                document_uri=overlay.uri,
                workspace_uri=workspace_uri,
                document_id=document_id,
                document_version=overlay.version,
                document_text=overlay.text,
                active_pack_id=(workspace.active_pack.pack_id),
                active_pack_version=(workspace.active_pack.pack_version),
                corpus_snapshot=(workspace.active_pack.corpus_snapshot),
            )
        except CodeActionError:
            return []
        return [action.as_dict() for action in actions]
