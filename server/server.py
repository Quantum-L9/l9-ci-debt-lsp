"""pygls LSP server — L9 CI-debt diagnostics and code actions."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from lsprotocol.types import (
    CODE_ACTION,
    INITIALIZE,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_SAVE,
    CodeActionOptions,
    CodeActionParams,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    DidSaveTextDocumentParams,
    InitializeParams,
    InitializeResult,
    ServerCapabilities,
    TextDocumentSyncKind,
)
from pygls.server import LanguageServer

from code_actions import compute_code_actions
from diagnostics import compute_diagnostics
from rules_loader import RulesLoader

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("l9-ci-debt-lsp")

DEFAULT_RULES_PATH = Path(__file__).parent.parent / "rules" / "compiled_rules.json"


def make_server(rules_path: Path) -> LanguageServer:
    loader = RulesLoader(rules_path)
    server = LanguageServer("l9-ci-debt-lsp", "v0.1.0")

    @server.feature(INITIALIZE)
    def on_initialize(params: InitializeParams) -> InitializeResult:
        log.info("L9 CI-Debt LSP initializing — %d rules loaded", len(loader.rules))
        return InitializeResult(
            capabilities=ServerCapabilities(
                text_document_sync=TextDocumentSyncKind.Full,
                code_action_provider=CodeActionOptions(
                    code_action_kinds=["quickfix"]
                ),
            )
        )

    @server.feature(TEXT_DOCUMENT_DID_OPEN)
    def did_open(params: DidOpenTextDocumentParams) -> None:
        _publish(server, loader, params.text_document.uri, params.text_document.text)

    @server.feature(TEXT_DOCUMENT_DID_SAVE)
    def did_save(params: DidSaveTextDocumentParams) -> None:
        doc = server.workspace.get_document(params.text_document.uri)
        _publish(server, loader, params.text_document.uri, doc.source)

    @server.feature(TEXT_DOCUMENT_DID_CHANGE)
    def did_change(params: DidChangeTextDocumentParams) -> None:
        if params.content_changes:
            _publish(
                server,
                loader,
                params.text_document.uri,
                params.content_changes[-1].text,
            )

    @server.feature(CODE_ACTION)
    def code_action(params: CodeActionParams):
        doc = server.workspace.get_document(params.text_document.uri)
        return compute_code_actions(doc.source, params, loader.rules)

    # Custom notification: reload rules without restarting server
    @server.command("l9/rulesRefreshed")
    def rules_refreshed(params) -> None:  # type: ignore[type-arg]
        new_path = Path(params.get("rulesPath", rules_path))
        loader.reload(new_path)
        log.info("Rules reloaded from %s — %d rules active", new_path, len(loader.rules))

    return server


def _publish(server: LanguageServer, loader: RulesLoader, uri: str, text: str) -> None:
    diagnostics = compute_diagnostics(text, uri, loader.rules)
    server.publish_diagnostics(uri, diagnostics)


def main() -> None:
    parser = argparse.ArgumentParser(description="L9 CI-Debt LSP Server")
    parser.add_argument(
        "--rules",
        type=Path,
        default=DEFAULT_RULES_PATH,
        help="Path to compiled_rules.json",
    )
    args = parser.parse_args()
    server = make_server(args.rules)
    log.info("L9 CI-Debt LSP server starting — rules: %s", args.rules)
    server.start_io()


if __name__ == "__main__":
    main()
