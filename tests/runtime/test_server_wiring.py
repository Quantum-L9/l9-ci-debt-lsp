from __future__ import annotations

from pathlib import Path

import pytest
from lsprotocol.types import (
    CodeActionContext,
    CodeActionParams,
    Position,
    Range,
    TextDocumentIdentifier,
)

import l9_debt_lsp.server as server_module
from l9_debt_lsp import __version__
from l9_debt_lsp.packs.paths import StatePaths


@pytest.fixture
def isolated_telemetry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the module-level server telemetry at a temp state root.

    Keeps ``l9/telemetry/report`` tests hermetic (no writes to the real user
    state directory) and resets the lazily-constructed singleton.
    """
    monkeypatch.setattr(server_module, "state_paths", StatePaths(tmp_path))
    monkeypatch.setattr(server_module, "_effectiveness", None)


def test_server_version_tracks_package_version() -> None:
    assert server_module.SERVER_VERSION == __version__


def test_dormant_features_are_registered() -> None:
    features = set(server_module.server.lsp.fm.features)
    # These handlers were built but never wired before the preflight pass.
    assert "textDocument/codeAction" in features
    assert "l9/health" in features
    assert "l9/telemetry/report" in features
    # Existing lifecycle handlers remain wired.
    for method in (
        "initialize",
        "textDocument/didOpen",
        "textDocument/didChange",
        "textDocument/didClose",
    ):
        assert method in features


def test_initialize_advertises_a_backed_code_action_provider() -> None:
    result = server_module.initialize(None)  # type: ignore[arg-type]
    provider = result.capabilities.code_action_provider
    assert provider is not None
    # The advertised quickfix provider now has a registered handler behind it.
    assert "textDocument/codeAction" in server_module.server.lsp.fm.features


def test_bootstrap_pack_is_the_unconfigured_placeholder() -> None:
    pack = server_module.bootstrap_pack()
    assert pack.pack_version == "unconfigured"
    assert pack.pack_id.startswith("pack_")


def test_resolve_pack_context_falls_back_to_bootstrap_when_no_active_pack() -> None:
    # No pack is activated under the default state root in the test environment.
    pack = server_module.resolve_pack_context()
    assert pack.pack_version == "unconfigured"


def test_configured_active_pack_id_is_none_without_activation() -> None:
    assert server_module.configured_active_pack_id() is None


def test_plain_coerces_namespaces_and_nested_containers() -> None:
    class Namespace:
        def __init__(self) -> None:
            self.a = 1
            self.b = [{"c": 2}]

    coerced = server_module._plain(Namespace())
    assert coerced == {"a": 1, "b": [{"c": 2}]}


def test_health_handler_reports_degraded_without_active_pack() -> None:
    health = server_module.l9_health(None)
    assert health["schema_version"] == "l9.runtime-health/v1"
    assert health["status"] == "degraded"
    assert health["active_pack_id"] is None
    assert health["limitations"]


def test_code_action_handler_returns_empty_for_unknown_document() -> None:
    params = CodeActionParams(
        text_document=TextDocumentIdentifier(uri="file:///unknown.py"),
        range=Range(start=Position(0, 0), end=Position(0, 0)),
        context=CodeActionContext(diagnostics=[]),
    )
    assert server_module.code_action(params) == []


def test_telemetry_report_ignores_payload_without_event(
    isolated_telemetry: None,
) -> None:
    result = server_module.l9_telemetry_report({"diagnostic": {"data": {}}})
    assert result["status"] == "ignored"


def test_telemetry_report_accepts_diagnostic_shown_but_persists_nothing(
    isolated_telemetry: None,
) -> None:
    # Default policy is disabled: the event is accepted and dispatched, but the
    # underlying service persists nothing.
    diagnostic = {
        "data": {
            "rule_pack_id": "pack_" + "a" * 64,
            "rule_pack_version": "1.0.0",
            "corpus_snapshot": "cs_" + "b" * 64,
            "canonical_rule_id": "L9-RULE-1",
            "provider_rule_id": "provider-1",
            "finding_id": "finding_" + "c" * 32,
            "analysis_request_id": "request_" + "d" * 32,
            "limitations": [],
        }
    }
    result = server_module.l9_telemetry_report(
        {"event": "diagnostic_shown", "diagnostic": diagnostic}
    )
    assert result["status"] == "accepted"
    assert result["event"] == "diagnostic_shown"
    assert server_module.effectiveness_telemetry().service.health()["status"] == (
        "disabled"
    )


def test_telemetry_report_reports_error_for_unsupported_event(
    isolated_telemetry: None,
) -> None:
    # Unsupported events must never propagate an exception to the editor.
    result = server_module.l9_telemetry_report({"event": "does_not_exist"})
    assert result["status"] == "error"
