from __future__ import annotations
from pathlib import Path
from typing import Any
from l9_debt_lsp.contracts.schema import SchemaValidator
from .errors import PackRetiredError
from .jsonio import load_json, write_canonical_json
EMPTY_REGISTRY = {
    "schema_version": "l9.retired-pack-registry/v1",
    "retired": [],
}
class RetirementRegistry:
    def __init__(
        self,
        path: Path,
        schema_path: Path,
    ) -> None:
        self.path = path
        self.schema_path = schema_path
    def initialize(self) -> None:
        if not self.path.exists():
            write_canonical_json(
                self.path,
                EMPTY_REGISTRY,
            )
    def load(self) -> dict[str, Any]:
        self.initialize()
        document = load_json(self.path)
        SchemaValidator(self.schema_path).validate(document)
        return document
    def require_not_retired(
        self,
        *,
        pack_id: str,
        pack_version: str,
    ) -> None:
        document = self.load()
        for entry in document["retired"]:
            if (
                entry["pack_id"] == pack_id
                or (
                    entry["pack_version"] == pack_version
                    and entry["pack_id"] == pack_id
                )
            ):
                raise PackRetiredError(
                    f"defense pack is retired: "
                    f"{pack_id} ({pack_version})"
                )
