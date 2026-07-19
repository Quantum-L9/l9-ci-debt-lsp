from __future__ import annotations

from typing import Any

from .delivery_state import DeliveryStateStore
from .models import TelemetryPolicy
from .spool import TelemetrySpool


def telemetry_health(
    *,
    policy: TelemetryPolicy,
    spool: TelemetrySpool,
    delivery_state: DeliveryStateStore,
) -> dict[str, Any]:
    statistics = spool.statistics()
    state = delivery_state.load()
    limitations = list(policy.limitations)
    limitations.extend(state.get("limitations", []))
    if policy.mode == "disabled":
        status = "disabled"
    elif limitations:
        status = "degraded"
    else:
        status = "healthy"
    return {
        "schema_version": "l9.telemetry-health/v1",
        "status": status,
        "policy_mode": policy.mode,
        "consent_state": policy.consent,
        "queued_event_count": statistics["queued_event_count"],
        "queued_bytes": statistics["queued_bytes"],
        "oldest_event_age_seconds": statistics["oldest_event_age_seconds"],
        "dead_letter_count": statistics["dead_letter_count"],
        "last_delivery_status": state.get("last_delivery_status"),
        "last_successful_delivery_at": state.get("last_successful_delivery_at"),
        "limitations": sorted(set(limitations)),
    }
