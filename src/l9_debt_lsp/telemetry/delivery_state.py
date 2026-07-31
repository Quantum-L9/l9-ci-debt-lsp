from __future__ import annotations

from pathlib import Path
from typing import Any

from l9_debt_lsp.packs.jsonio import (
    load_json,
    write_canonical_json,
)

DEFAULT_STATE: dict[str, Any] = {
    "schema_version": "l9.telemetry-delivery-state/v1",
    "last_attempt_at": None,
    "last_successful_delivery_at": None,
    "last_delivery_status": None,
    "consecutive_failures": 0,
    "next_attempt_at": None,
    "limitations": [],
}


class DeliveryStateStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, Any]:
        if not self.path.is_file():
            write_canonical_json(
                self.path,
                DEFAULT_STATE,
            )
        return load_json(self.path)

    def save(self, state: dict[str, Any]) -> None:
        write_canonical_json(self.path, state)
