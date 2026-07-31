from __future__ import annotations

from pathlib import Path

import pytest

from l9_debt_lsp.analysis.errors import WorkspaceNotFoundError
from l9_debt_lsp.packs.paths import StatePaths
from l9_debt_lsp.runtime.analysis_service import (
    build_default_runtime,
    load_active_pack_context,
)
from l9_debt_lsp.runtime.code_action_service import CodeActionService
from l9_debt_lsp.runtime.health import runtime_health
from l9_debt_lsp.runtime.state import PackInstallationState
from l9_debt_lsp.runtime.telemetry_service import EffectivenessTelemetry

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "schemas/lsp"


def test_build_default_runtime_is_fail_closed() -> None:
    runtime = build_default_runtime()
    assert runtime.workspaces is not None
    # No SDK binding configured: the default adapter is the unavailable one.
    assert runtime.workspaces._workspaces == {}


def test_load_active_pack_context_raises_without_activation(tmp_path: Path) -> None:
    paths = StatePaths(tmp_path)
    with pytest.raises(RuntimeError):
        load_active_pack_context(paths=paths, schema_root=SCHEMA_ROOT)


def test_runtime_health_degrades_without_active_pack() -> None:
    runtime = build_default_runtime()
    health = runtime_health(runtime, active_pack_id=None)
    assert health["status"] == "degraded"
    assert health["workspace_count"] == 0
    assert health["open_document_count"] == 0
    assert health["limitations"]


def test_runtime_health_is_healthy_with_active_pack() -> None:
    runtime = build_default_runtime()
    health = runtime_health(runtime, active_pack_id="pack_" + "a" * 64)
    assert health["status"] == "healthy"
    assert health["active_pack_id"] == "pack_" + "a" * 64
    assert health["limitations"] == []


def test_code_action_service_is_graceful_for_unknown_workspace(
    tmp_path: Path,
) -> None:
    runtime = build_default_runtime()
    service = CodeActionService(
        runtime=runtime,
        schema_root=SCHEMA_ROOT,
        packs_root=StatePaths(tmp_path).packs,
    )
    with pytest.raises(WorkspaceNotFoundError):
        # No workspace has been opened; the service does not invent actions, it
        # surfaces the missing-workspace lookup error to its caller.
        service.actions_for_diagnostic(
            workspace_id="workspace_" + "0" * 64,
            workspace_uri="file:///ws",
            document_id="document_" + "0" * 64,
            diagnostic={"data": {}},
        )


def test_effectiveness_telemetry_is_disabled_by_default(tmp_path: Path) -> None:
    telemetry = EffectivenessTelemetry(
        state_paths=StatePaths(tmp_path),
        schema_root=SCHEMA_ROOT,
        client_name="test",
        client_version="1.0.0",
        lsp_version="1.0.0",
    )
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
    # Disabled policy: nothing is persisted.
    telemetry.diagnostic_shown(diagnostic)
    telemetry.diagnostic_dismissed(diagnostic)
    health = telemetry.service.health()
    assert health["policy_mode"] == "disabled"
    assert health["status"] == "disabled"
    assert health["queued_event_count"] == 0


def test_effectiveness_telemetry_persists_when_local_only(tmp_path: Path) -> None:
    telemetry = EffectivenessTelemetry(
        state_paths=StatePaths(tmp_path),
        schema_root=SCHEMA_ROOT,
        client_name="test",
        client_version="1.0.0",
        lsp_version="1.0.0",
    )
    from l9_debt_lsp.telemetry.models import TelemetryPolicy

    telemetry.service.policy_store.save(
        TelemetryPolicy(
            mode="local_only",
            consent="granted",
            endpoint=None,
            endpoint_allowlist=(),
            retention_days=30,
            organization_policy_id=None,
            limitations=(),
        )
    )
    provenance = {
        "rule_pack_id": "pack_" + "a" * 64,
        "rule_pack_version": "1.0.0",
        "corpus_snapshot": "cs_" + "b" * 64,
        "canonical_rule_id": "L9-RULE-1",
        "provider_rule_id": "provider-1",
        "finding_id": "finding_" + "c" * 32,
        "analysis_request_id": "request_" + "d" * 32,
        "action_id": "action_" + "e" * 32,
        "template_id": "template-1",
        "limitations": [],
    }
    telemetry.quick_fix_applied(provenance)
    telemetry.quick_fix_outcome(provenance=provenance, outcome="finding_resolved")
    telemetry.analysis_latency(
        {
            "latency_ms": 12.0,
            "status": "complete",
            "latency_class": "fast",
            "active_pack_id": "pack_" + "a" * 64,
            "request_id": "request_" + "d" * 32,
        }
    )
    health = telemetry.service.health()
    assert health["policy_mode"] == "local_only"
    assert health["queued_event_count"] >= 3


def test_pack_installation_state_projection_round_trips() -> None:
    state = PackInstallationState(
        pack_id="pack_" + "a" * 64,
        pack_version="1.0.0",
        state="active",
        compatibility_state="compatible",
        installed_path=Path("/var/lsp/packs/pack"),
        limitations=(),
    )
    payload = state.as_dict()
    assert payload["schema_version"] == "l9.pack-installation-state/v1"
    assert payload["state"] == "active"
    assert payload["installed_path"].endswith("packs/pack")
    assert payload["limitations"] == []
