from __future__ import annotations

import json
from pathlib import Path

import pytest

from l9_debt_lsp.packs.activation import ActivationManager
from l9_debt_lsp.packs.errors import PackValidationError
from l9_debt_lsp.packs.paths import StatePaths

ROOT = Path(__file__).resolve().parents[2]


def test_invalid_target_does_not_replace_active_pack(
    tmp_path: Path,
) -> None:
    paths = StatePaths(tmp_path / "state")
    paths.initialize()
    active_id = "pack_" + "a" * 64
    root = paths.packs / active_id
    root.mkdir(parents=True)
    installation = {
        "schema_version": ("l9.pack-installation-record/v1"),
        "pack_id": active_id,
        "pack_version": "1.0.0",
        "archive_sha256": "b" * 64,
        "manifest_sha256": "c" * 64,
        "signer_key_id": "key_" + "d" * 64,
        "compatibility_state": "compatible",
        "installed_at": "2026-07-18T00:00:00Z",
        "content_hashes": {},
        "limitations": [],
    }
    defense_pack = {
        "pack_id": active_id,
        "version": "1.0.0",
        "corpus_snapshot": "cs_" + "e" * 64,
        "compiler_version": "1.0.0",
        "taxonomy_version": "1.0.0",
        "SDK_contract_version": ("l9.integration-contract/v1"),
    }
    for name, document in {
        "manifest.json": {},
        "defense-pack.json": defense_pack,
        "compatibility.json": {},
        "checksums.json": {},
        "installation.json": installation,
    }.items():
        (root / name).write_text(
            json.dumps(document),
            encoding="utf-8",
        )
    (root / "archive.sha256").write_text(
        "b" * 64 + "\n",
        encoding="ascii",
    )
    manager = ActivationManager(
        paths=paths,
        schema_root=ROOT / "schemas/lsp",
    )
    manager.activate(active_id)
    with pytest.raises(PackValidationError):
        manager.activate("pack_" + "f" * 64)
    assert manager.load_active().pack_id == active_id
