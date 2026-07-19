from __future__ import annotations

import json
from pathlib import Path

from l9_debt_lsp.contracts.descriptor import (
    descriptor_from_defense_pack,
)

ROOT = Path(__file__).resolve().parents[2]


def test_descriptor_preserves_pack_lineage() -> None:
    pack = json.loads(
        (ROOT / "tests/fixtures/packs/compatible-defense-pack.json").read_text(
            encoding="utf-8"
        )
    )
    descriptor = descriptor_from_defense_pack(pack)
    assert descriptor.pack_id == pack["pack_id"]
    assert descriptor.pack_version == pack["version"]
    assert descriptor.protocol == "l9.debt-defense/v1"
    assert descriptor.corpus_snapshot == pack["corpus_snapshot"]
    assert descriptor.analysis_run == pack["analysis_run"]
    assert descriptor.compilation_id == pack["compilation_id"]
    assert descriptor.sdk_contract_version == ("l9.integration-contract/v1")
    assert descriptor.runtime_rule_kinds == ("ast_grep",)
