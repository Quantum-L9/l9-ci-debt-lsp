from __future__ import annotations

from pathlib import Path

import pytest

from l9_debt_lsp.telemetry.errors import (
    TelemetryPolicyError,
)
from l9_debt_lsp.telemetry.models import TelemetryPolicy
from l9_debt_lsp.telemetry.policy import (
    TelemetryPolicyStore,
)

ROOT = Path(__file__).resolve().parents[2]


def test_default_policy_is_disabled(tmp_path: Path) -> None:
    store = TelemetryPolicyStore(
        path=tmp_path / "policy.json",
        schema_path=(ROOT / "schemas/lsp/telemetry-policy.schema.json"),
    )
    policy = store.load()
    assert policy.mode == "disabled"
    assert policy.persistence_enabled is False
    assert policy.delivery_enabled is False


def test_delivery_requires_https_allowlist(
    tmp_path: Path,
) -> None:
    store = TelemetryPolicyStore(
        path=tmp_path / "policy.json",
        schema_path=(ROOT / "schemas/lsp/telemetry-policy.schema.json"),
    )
    policy = TelemetryPolicy(
        mode="user_opt_in",
        consent="granted",
        endpoint="https://telemetry.example.test/v1",
        endpoint_allowlist=("https://different.example.test/",),
        retention_days=30,
        organization_policy_id=None,
        limitations=(),
    )
    with pytest.raises(TelemetryPolicyError):
        store.save(policy)
