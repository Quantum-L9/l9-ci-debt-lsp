from __future__ import annotations

from l9_debt_lsp.telemetry.events import EventFactory
from l9_debt_lsp.telemetry.models import (
    TelemetryContext,
)


def test_event_identity_is_unique_per_sequence() -> None:
    factory = EventFactory(
        TelemetryContext(
            installation_id=("installation_" + "a" * 64),
            session_id="session_" + "b" * 64,
            client_name="vscode",
            client_version="1.0",
            lsp_version="1.0.0",
        )
    )
    first = factory.create(
        event_type="diagnostic_shown",
        rule_pack_id="pack_" + "c" * 64,
        canonical_rule_id="l9.example",
        finding_id="finding-1",
    )
    second = factory.create(
        event_type="diagnostic_shown",
        rule_pack_id="pack_" + "c" * 64,
        canonical_rule_id="l9.example",
        finding_id="finding-1",
    )
    assert first.event_id != second.event_id
    assert first.sequence == 1
    assert second.sequence == 2
