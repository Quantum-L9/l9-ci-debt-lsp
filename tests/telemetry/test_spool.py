from __future__ import annotations

from pathlib import Path

from l9_debt_lsp.telemetry.events import EventFactory
from l9_debt_lsp.telemetry.models import (
    TelemetryContext,
)
from l9_debt_lsp.telemetry.spool import TelemetrySpool


def factory() -> EventFactory:
    return EventFactory(
        TelemetryContext(
            installation_id=("installation_" + "a" * 64),
            session_id="session_" + "b" * 64,
            client_name="test",
            client_version="1",
            lsp_version="1.0.0",
        )
    )


def test_spool_persists_and_acknowledges(
    tmp_path: Path,
) -> None:
    events = tmp_path / "events"
    dead = tmp_path / "dead"
    events.mkdir()
    dead.mkdir()
    spool = TelemetrySpool(
        event_root=events,
        dead_letter_root=dead,
        retention_days=30,
    )
    event = factory().create(
        event_type="diagnostic_shown",
        canonical_rule_id="l9.example",
        finding_id="finding-1",
    )
    path = spool.append(event)
    assert path.is_file()
    batch = spool.batch()
    assert len(batch) == 1
    assert batch[0][1]["event_id"] == event.event_id
    spool.acknowledge([path])
    assert not path.exists()
