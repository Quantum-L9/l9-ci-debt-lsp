from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lsprotocol.types import (
    CodeAction,
    CodeActionOptions,
    CodeActionParams,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    InitializeParams,
    InitializeResult,
    PublishDiagnosticsParams,
    ServerCapabilities,
    ServerInfo,
    TextDocumentSyncKind,
)
from pygls.lsp.server import LanguageServer

from l9_debt_lsp import __version__
from l9_debt_lsp.actions.lsp_types import to_lsp_code_action
from l9_debt_lsp.analysis.identity import (
    document_identity,
    workspace_identity,
)
from l9_debt_lsp.analysis.models import PackContext
from l9_debt_lsp.diagnostics.lsp_types import (
    to_lsp_diagnostic,
)
from l9_debt_lsp.diagnostics.publisher import (
    DiagnosticPublisher,
)
from l9_debt_lsp.packs.paths import (
    StatePaths,
    default_state_root,
)
from l9_debt_lsp.runtime.analysis_service import (
    build_default_runtime,
    load_active_pack_context,
)
from l9_debt_lsp.runtime.capabilities import (
    phase_capabilities,
)
from l9_debt_lsp.runtime.code_action_service import (
    CodeActionService,
)
from l9_debt_lsp.runtime.diagnostic_service import (
    DiagnosticService,
)
from l9_debt_lsp.runtime.health import runtime_health
from l9_debt_lsp.runtime.telemetry_service import (
    EffectivenessTelemetry,
)

SERVER_NAME = "l9-ci-debt-lsp"
SERVER_VERSION = __version__
SCHEMA_ROOT = Path("schemas/lsp").resolve()

server = LanguageServer(
    SERVER_NAME,
    SERVER_VERSION,
)
runtime = build_default_runtime()
state_paths = StatePaths(default_state_root())


async def publish_callback(
    uri: str,
    diagnostics: list[dict[str, object]],
) -> None:
    server.text_document_publish_diagnostics(
        PublishDiagnosticsParams(
            uri=uri,
            diagnostics=[to_lsp_diagnostic(value) for value in diagnostics],
        )
    )


publisher = DiagnosticPublisher(
    workspaces=runtime.workspaces,
    callback=publish_callback,
)
diagnostic_service = DiagnosticService(
    runtime=runtime,
    publisher=publisher,
    schema_root=SCHEMA_ROOT,
)
code_action_service = CodeActionService(
    runtime=runtime,
    schema_root=SCHEMA_ROOT,
    packs_root=state_paths.packs,
)
workspace_by_document: dict[str, str] = {}
workspace_uri_by_id: dict[str, str] = {}

# Effectiveness telemetry is constructed lazily so that a server run with the
# default (disabled) policy leaves no telemetry footprint on disk. It is only
# instantiated when a telemetry-aware editor client reports a lifecycle event
# via ``l9/telemetry/report`` (ADR-LSP-021: telemetry is disabled by default).
_effectiveness: EffectivenessTelemetry | None = None


def effectiveness_telemetry() -> EffectivenessTelemetry:
    global _effectiveness
    if _effectiveness is None:
        _effectiveness = EffectivenessTelemetry(
            state_paths=state_paths,
            schema_root=SCHEMA_ROOT,
            client_name=SERVER_NAME,
            client_version=SERVER_VERSION,
            lsp_version=__version__,
        )
    return _effectiveness


def bootstrap_pack() -> PackContext:
    return PackContext(
        pack_id="pack_" + "0" * 64,
        pack_version="unconfigured",
        corpus_snapshot="cs_" + "0" * 64,
        compiler_version="unconfigured",
        taxonomy_version="unconfigured",
        sdk_contract_version="l9.integration-contract/v1",
    )


def resolve_pack_context() -> PackContext:
    """Load the activated defense pack, or fall back to the placeholder.

    When an operator has installed and activated a pack (via the contracts
    CLI), the running server picks it up from state instead of serving the
    unconfigured bootstrap placeholder.
    """
    try:
        return load_active_pack_context(
            paths=state_paths,
            schema_root=SCHEMA_ROOT,
        )
    except RuntimeError:
        return bootstrap_pack()


def configured_active_pack_id() -> str | None:
    try:
        return load_active_pack_context(
            paths=state_paths,
            schema_root=SCHEMA_ROOT,
        ).pack_id
    except RuntimeError:
        return None


def _plain(value: Any) -> Any:
    """Coerce pygls-decoded params (namespaces) into plain JSON structures."""
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if hasattr(value, "__dict__"):
        return {key: _plain(item) for key, item in vars(value).items()}
    return value


@server.feature("initialize")
def initialize(
    _params: InitializeParams,
) -> InitializeResult:
    return InitializeResult(
        capabilities=ServerCapabilities(
            text_document_sync=TextDocumentSyncKind.Full,
            code_action_provider=CodeActionOptions(
                code_action_kinds=["quickfix"],
                resolve_provider=False,
            ),
        ),
        server_info=ServerInfo(
            name=SERVER_NAME,
            version=SERVER_VERSION,
        ),
    )


@server.feature("textDocument/didOpen")
async def did_open(
    params: DidOpenTextDocumentParams,
) -> None:
    document = params.text_document
    workspace_uri = server.workspace.root_uri or document.uri.rsplit("/", 1)[0]
    workspace_id = workspace_identity(workspace_uri)
    try:
        runtime.workspaces.get_workspace_nowait(workspace_id)
    except Exception:
        await runtime.open_workspace(
            workspace_uri=workspace_uri,
            pack=resolve_pack_context(),
        )
    workspace_uri_by_id[workspace_id] = workspace_uri
    metadata = await runtime.open_document(
        workspace_id=workspace_id,
        uri=document.uri,
        language_id=document.language_id,
        version=document.version,
        text=document.text,
    )
    workspace_by_document[metadata["document_id"]] = workspace_id
    await diagnostic_service.evaluate_and_publish(
        workspace_id=workspace_id,
        document_id=metadata["document_id"],
    )


@server.feature("textDocument/didChange")
async def did_change(
    params: DidChangeTextDocumentParams,
) -> None:
    document_id = document_identity(params.text_document.uri)
    workspace_id = workspace_by_document.get(document_id)
    if workspace_id is None:
        return
    if not params.content_changes:
        return
    text = params.content_changes[-1].text
    version = params.text_document.version
    await runtime.update_document(
        workspace_id=workspace_id,
        document_id=document_id,
        version=version,
        text=text,
    )
    await diagnostic_service.evaluate_and_publish(
        workspace_id=workspace_id,
        document_id=document_id,
    )


@server.feature("textDocument/didClose")
async def did_close(
    params: DidCloseTextDocumentParams,
) -> None:
    uri = params.text_document.uri
    document_id = document_identity(uri)
    workspace_id = workspace_by_document.pop(
        document_id,
        None,
    )
    if workspace_id is None:
        return
    await diagnostic_service.close_document(
        workspace_id=workspace_id,
        document_id=document_id,
        document_uri=uri,
    )


@server.feature("textDocument/codeAction")
def code_action(
    params: CodeActionParams,
) -> list[CodeAction]:
    uri = params.text_document.uri
    document_id = document_identity(uri)
    workspace_id = workspace_by_document.get(document_id)
    if workspace_id is None:
        return []
    workspace_uri = workspace_uri_by_id.get(workspace_id)
    if workspace_uri is None:
        return []
    actions: list[CodeAction] = []
    for diagnostic in params.context.diagnostics:
        data = _plain(diagnostic.data)
        if not isinstance(data, dict):
            continue
        for action in code_action_service.actions_for_diagnostic(
            workspace_id=workspace_id,
            workspace_uri=workspace_uri,
            document_id=document_id,
            diagnostic={"data": data},
        ):
            actions.append(to_lsp_code_action(action))
    return actions


@server.feature("l9/health")
def l9_health(
    _params: Any,
) -> dict[str, Any]:
    return runtime_health(
        runtime,
        active_pack_id=configured_active_pack_id(),
    )


@server.feature("l9/telemetry/report")
def l9_telemetry_report(
    params: Any,
) -> dict[str, Any]:
    """Record an editor-reported effectiveness event.

    Telemetry is client-driven: the editor decides — subject to the user's
    consent policy — when a diagnostic was shown or a quick fix applied, and
    reports it here. Emission still fails closed: a disabled policy persists
    nothing, and any failure is swallowed so telemetry never blocks the editor
    (ADR-LSP-021 through ADR-LSP-023).
    """
    payload = _plain(params)
    if not isinstance(payload, dict):
        return {"status": "ignored", "reason": "invalid payload"}
    event = payload.get("event")
    if not isinstance(event, str):
        return {"status": "ignored", "reason": "missing event"}
    try:
        _dispatch_telemetry(effectiveness_telemetry(), event, payload)
    except Exception:
        return {"status": "error"}
    return {"status": "accepted", "event": event}


def _dispatch_telemetry(
    telemetry: EffectivenessTelemetry,
    event: str,
    payload: dict[str, Any],
) -> None:
    diagnostic = payload.get("diagnostic")
    provenance = payload.get("provenance")
    if event == "diagnostic_shown" and isinstance(diagnostic, dict):
        telemetry.diagnostic_shown(diagnostic)
    elif event == "diagnostic_dismissed" and isinstance(diagnostic, dict):
        telemetry.diagnostic_dismissed(diagnostic)
    elif event == "false_positive_disposition" and isinstance(diagnostic, dict):
        telemetry.disposition(
            diagnostic=diagnostic,
            disposition=str(payload.get("disposition", "unknown")),
        )
    elif event == "quick_fix_offered" and isinstance(payload.get("action"), dict):
        telemetry.quick_fix_offered(payload["action"])
    elif event == "quick_fix_applied" and isinstance(provenance, dict):
        telemetry.quick_fix_applied(provenance)
    elif event == "quick_fix_rejected" and isinstance(provenance, dict):
        telemetry.quick_fix_rejected(provenance)
    elif event == "quick_fix_outcome" and isinstance(provenance, dict):
        telemetry.quick_fix_outcome(
            provenance=provenance,
            outcome=str(payload.get("outcome", "outcome_unknown")),
        )
    elif event == "latency_bucket" and isinstance(payload.get("analysis"), dict):
        telemetry.analysis_latency(payload["analysis"])
    else:
        raise ValueError(f"unsupported telemetry event: {event}")


@server.feature("l9/serverCapabilities")
def l9_server_capabilities(
    _params: Any,
) -> dict[str, Any]:
    return phase_capabilities()


@server.command("l9.showServerCapabilities")
def show_server_capabilities(
    _arguments: list[Any],
) -> str:
    return json.dumps(
        phase_capabilities(),
        sort_keys=True,
        separators=(",", ":"),
    )


def main() -> None:
    server.start_io()


if __name__ == "__main__":
    main()
