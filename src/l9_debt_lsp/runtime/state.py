from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PackInstallationState:
    pack_id: str
    pack_version: str
    state: str
    compatibility_state: str
    installed_path: Path | None
    limitations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.pack-installation-state/v1",
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "state": self.state,
            "compatibility_state": self.compatibility_state,
            "installed_path": (
                self.installed_path.as_posix()
                if self.installed_path is not None
                else None
            ),
            "limitations": list(self.limitations),
        }
