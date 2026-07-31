from __future__ import annotations

import json
from pathlib import Path

from l9_debt_lsp.contracts.compatibility import (
    evaluate_compatibility,
)
from l9_debt_lsp.contracts.descriptor import (
    descriptor_from_defense_pack,
)

ROOT = Path(__file__).resolve().parents[2]


def load_pack() -> dict[str, object]:
    return json.loads(
        (ROOT / "tests/fixtures/packs/compatible-defense-pack.json").read_text(
            encoding="utf-8"
        )
    )


def test_compatible_pack_is_accepted() -> None:
    pack = load_pack()
    descriptor = descriptor_from_defense_pack(pack)
    result = evaluate_compatibility(
        descriptor=descriptor,
        compatibility=pack["compatibility"],
        platform_identity="linux-x86_64",
    )
    assert result.status == "compatible"
    assert all(result.checks.values())
    assert result.limitations == ()


def test_unsupported_platform_is_incompatible() -> None:
    pack = load_pack()
    descriptor = descriptor_from_defense_pack(pack)
    result = evaluate_compatibility(
        descriptor=descriptor,
        compatibility=pack["compatibility"],
        platform_identity="unsupported-platform",
    )
    assert result.status == "incompatible"
    assert result.checks["platform_supported"] is False


def test_incompatible_sdk_contract_is_rejected() -> None:
    pack = load_pack()
    pack["SDK_contract_version"] = "l9.integration-contract/v999"
    descriptor = descriptor_from_defense_pack(pack)
    result = evaluate_compatibility(
        descriptor=descriptor,
        compatibility=pack["compatibility"],
        platform_identity="linux-x86_64",
    )
    assert result.status == "incompatible"
    assert result.checks["sdk_contract_supported"] is False
    assert result.checks["sdk_matrix_contract_matches"] is False
