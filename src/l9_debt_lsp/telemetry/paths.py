from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from l9_debt_lsp.packs.paths import StatePaths


@dataclass(frozen=True)
class TelemetryPaths:
    state: StatePaths

    @property
    def root(self) -> Path:
        return self.state.root / "telemetry"

    @property
    def events(self) -> Path:
        return self.root / "events"

    @property
    def dead_letter(self) -> Path:
        return self.root / "dead-letter"

    @property
    def policy(self) -> Path:
        return self.root / "telemetry-policy.json"

    @property
    def installation_id(self) -> Path:
        return self.root / "installation-id.json"

    @property
    def delivery_state(self) -> Path:
        return self.root / "delivery-state.json"

    def initialize(self) -> None:
        for path in (
            self.root,
            self.events,
            self.dead_letter,
        ):
            path.mkdir(parents=True, exist_ok=True)
            path.chmod(0o700)
