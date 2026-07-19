from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lsprotocol.types import (
    CodeActionOptions,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    InitializeParams,
    InitializeResult,
    InitializeResultServerInfoType,
    ServerCapabilities,
    TextDocumentSyncKind,
)
from pygls.server import LanguageServer

from l9_debt_lsp.analysis.identity import (
    document_identity,
    workspace_identity,
)
from l9_debt_lsp.analysis.models import PackContext
from l9_debt_lsp.analysis.null_sdk import (
    UnavailableAnalysisSession,
)
from l9_debt_lsp.analysis.runtime import (
    IncrementalAnalysisRuntime,
)
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
from l9_debt_lsp.runtime.capabilities import (
    phase_capabilities,
)
from l9_debt_lsp.runtime.code_action_service import (
    CodeActionService,
)
from l9_debt_lsp.runtime.diagnostic_service import (
    DiagnosticService,
)

SERVER_NAME = "l9-ci-debt-lsp"
SERVER_VERSION = "0.4.0"
server = LanguageServer(
    SERVER_NAME,
    SERVER_VERSION,
)
runtime = IncrementalAnalysisRuntime(UnavailableAnalysisSession())


async def publish_callback(
    uri: str,
    diagnostics: list[dict[str, object]],
) -> None:
    server.publish_diagnostics(
        uri,
        [to_lsp_diagnostic(value) for value in diagnostics],
    )


publisher = DiagnosticPublisher(
    workspaces=runtime.workspaces,
    callback=publish_callback,
)
diagnostic_service = DiagnosticService(
    runtime=runtime,
    publisher=publisher,
    schema_root=Path("schemas/lsp").resolve(),
)
state_paths = StatePaths(default_state_root())
code_action_service = CodeActionService(
    runtime=runtime,
    schema_root=Path("schemas/lsp").resolve(),
    packs_root=state_paths.packs,
)
workspace_by_document: dict[str, str] = {}


def bootstrap_pack() -> PackContext:
    return PackContext(
        pack_id="pack_" + "0" * 64,
        pack_version="unconfigured",
        corpus_snapshot="cs_" + "0" * 64,
        compiler_version="unconfigured",
        taxonomy_version="unconfigured",
        sdk_contract_version="l9.integration-contract/v1",
    )


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
        server_info=InitializeResultServerInfoType(
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
            pack=bootstrap_pack(),
        )
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
