from __future__ import annotations

import secrets
from pathlib import Path
from typing import Any

from l9_debt_lsp.packs.hashing import namespaced_hash
from l9_debt_lsp.packs.jsonio import (
    load_json,
    write_canonical_json,
)


def random_identity(prefix: str) -> str:
    return prefix + secrets.token_hex(32)


class InstallationIdentityStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load_or_create(self) -> str:
        if self.path.is_file():
            document = load_json(self.path)
            value = document.get("installation_id")
            if (
                isinstance(value, str)
                and value.startswith("installation_")
                and len(value) == len("installation_") + 64
            ):
                return value
        value = random_identity("installation_")
        write_canonical_json(
            self.path,
            {
                "schema_version": ("l9.telemetry-installation-id/v1"),
                "installation_id": value,
            },
        )
        return value

    def rotate(self) -> str:
        value = random_identity("installation_")
        write_canonical_json(
            self.path,
            {
                "schema_version": ("l9.telemetry-installation-id/v1"),
                "installation_id": value,
            },
        )
        return value


def event_identity(value: dict[str, Any]) -> str:
    return namespaced_hash("event_", value)
