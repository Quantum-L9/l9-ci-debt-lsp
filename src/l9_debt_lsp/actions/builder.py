from __future__ import annotations

from pathlib import Path
from typing import Any

from l9_debt_lsp.contracts.canonical import canonical_json
from l9_debt_lsp.packs.hashing import (
    namespaced_hash,
    sha256_bytes,
)

from .errors import (
    CodeActionSuppressed,
    StaleDiagnosticError,
)
from .models import (
    BoundedCodeAction,
    CodeActionProvenance,
)
from .positions import validate_edits
from .preview import build_preview
from .protected_paths import require_editable_path
from .templates import TemplateParser

MAX_ACTIONS_PER_DIAGNOSTIC = 5


class CodeActionBuilder:
    def __init__(self, schema_root: Path) -> None:
        self._parser = TemplateParser(schema_root)

    def build(
        self,
        *,
        diagnostic: dict[str, Any],
        templates: list[dict[str, Any]],
        document_uri: str,
        workspace_uri: str,
        document_id: str,
        document_version: int,
        document_text: str,
        active_pack_id: str,
        active_pack_version: str,
        corpus_snapshot: str,
    ) -> tuple[BoundedCodeAction, ...]:
        data = diagnostic.get("data")
        if not isinstance(data, dict):
            raise CodeActionSuppressed("diagnostic does not contain canonical L9 data")
        self._validate_diagnostic_binding(
            data=data,
            document_id=document_id,
            document_version=document_version,
            active_pack_id=active_pack_id,
            active_pack_version=active_pack_version,
        )
        if data["analysis_status"] != "complete":
            raise CodeActionSuppressed(
                "code actions are suppressed for incomplete analysis"
            )
        relative_path = require_editable_path(
            document_uri=document_uri,
            workspace_uri=workspace_uri,
        )
        actions: list[BoundedCodeAction] = []
        for raw_template in templates:
            template = self._parser.parse(raw_template)
            if template.canonical_rule_id != data["canonical_rule_id"]:
                continue
            edits = validate_edits(
                text=document_text,
                edits=template.edits,
            )
            summary, diff, limitations = build_preview(
                relative_path=relative_path,
                text=document_text,
                template=template,
            )
            edit_payload = {
                "document_uri": document_uri,
                "document_version": document_version,
                "edits": [edit.as_dict() for edit in edits],
            }
            edit_digest = sha256_bytes(canonical_json(edit_payload))
            action_id = namespaced_hash(
                "action_",
                {
                    "template_id": template.template_id,
                    "finding_id": data["finding_id"],
                    "document_identity": document_id,
                    "document_version": document_version,
                    "rule_pack_id": active_pack_id,
                    "edit_digest": edit_digest,
                },
            )
            provenance = CodeActionProvenance(
                action_id=action_id,
                template_id=template.template_id,
                finding_id=data["finding_id"],
                canonical_rule_id=data["canonical_rule_id"],
                provider_rule_id=data["provider_rule_id"],
                document_identity=document_id,
                document_version=document_version,
                rule_pack_id=active_pack_id,
                rule_pack_version=active_pack_version,
                corpus_snapshot=corpus_snapshot,
                analysis_request_id=data["analysis_request_id"],
                edit_digest=edit_digest,
                limitations=limitations,
            )
            actions.append(
                BoundedCodeAction(
                    title=template.title,
                    document_uri=document_uri,
                    edits=edits,
                    preview_summary=summary,
                    preview_diff=diff,
                    preview_limitations=limitations,
                    provenance=provenance,
                    is_preferred=(
                        template.safety == "deterministic" and not limitations
                    ),
                )
            )
        actions.sort(
            key=lambda action: (
                not action.is_preferred,
                action.title,
                action.provenance.template_id,
                action.provenance.action_id,
            )
        )
        return tuple(actions[:MAX_ACTIONS_PER_DIAGNOSTIC])

    @staticmethod
    def _validate_diagnostic_binding(
        *,
        data: dict[str, Any],
        document_id: str,
        document_version: int,
        active_pack_id: str,
        active_pack_version: str,
    ) -> None:
        required = (
            "finding_id",
            "canonical_rule_id",
            "provider_rule_id",
            "document_identity",
            "document_version",
            "rule_pack_id",
            "rule_pack_version",
            "corpus_snapshot",
            "analysis_request_id",
            "analysis_status",
        )
        missing = [field for field in required if field not in data]
        if missing:
            raise CodeActionSuppressed(f"diagnostic data is incomplete: {missing}")
        if data["document_identity"] != document_id:
            raise StaleDiagnosticError("diagnostic document identity is stale")
        if data["document_version"] != document_version:
            raise StaleDiagnosticError("diagnostic document version is stale")
        if data["rule_pack_id"] != active_pack_id:
            raise StaleDiagnosticError("diagnostic pack identity is stale")
        if data["rule_pack_version"] != active_pack_version:
            raise StaleDiagnosticError("diagnostic pack version is stale")
