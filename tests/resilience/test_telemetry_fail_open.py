from __future__ import annotations

from pathlib import Path

from l9_debt_lsp.telemetry.models import TelemetryPolicy


def test_disabled_telemetry_requires_no_endpoint(
    tmp_path: Path,
) -> None:
    policy = TelemetryPolicy(
        mode="disabled",
        consent="not_granted",
        endpoint=None,
        endpoint_allowlist=(),
        retention_days=30,
        organization_policy_id=None,
        limitations=(),
    )
    assert policy.persistence_enabled is False
    assert policy.delivery_enabled is False
