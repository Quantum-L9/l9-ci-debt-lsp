from __future__ import annotations

import json
from pathlib import Path

import pytest

from l9_debt_lsp.contracts.descriptor import (
    descriptor_from_defense_pack,
)
from l9_debt_lsp.contracts.errors import SchemaValidationError
from l9_debt_lsp.contracts.schema import SchemaValidator

ROOT = Path(__file__).resolve().parents[2]


def test_pack_descriptor_schema_accepts_projected_pack() -> None:
    pack = json.loads(
        (ROOT / "tests/fixtures/packs/compatible-defense-pack.json").read_text(
            encoding="utf-8"
        )
    )
    descriptor = descriptor_from_defense_pack(pack).as_dict()
    validator = SchemaValidator(ROOT / "schemas/lsp/pack-descriptor.schema.json")
    validator.validate(descriptor)


def test_pack_descriptor_schema_rejects_invalid_identity() -> None:
    pack = json.loads(
        (ROOT / "tests/fixtures/packs/compatible-defense-pack.json").read_text(
            encoding="utf-8"
        )
    )
    descriptor = descriptor_from_defense_pack(pack).as_dict()
    descriptor["pack_id"] = "mutable-latest"
    validator = SchemaValidator(ROOT / "schemas/lsp/pack-descriptor.schema.json")
    with pytest.raises(SchemaValidationError):
        validator.validate(descriptor)
