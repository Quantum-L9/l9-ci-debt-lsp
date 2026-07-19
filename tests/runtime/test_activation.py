from __future__ import annotations

import json
from pathlib import Path

from l9_debt_lsp.packs.activation import ActivationManager
from l9_debt_lsp.packs.paths import StatePaths

ROOT = Path(__file__).resolve().parents[2]


def create_installed_pack(
    paths: StatePaths,
    *,
    pack_id: str,
    version: str,
    archive_hash: str,
) -> None:
    root = paths.packs / pack_id
    root.mkdir(parents=True)
    defense_pack = {
        "pack_id": pack_id,
        "version": version,
        "corpus_snapshot": ("cs_" + "b" * 64),
        "compiler_version": "1.0.0",
        "taxonomy_version": "1.0.0",
        "SDK_contract_version": ("l9.integration-contract/v1"),
    }
    installation = {
        "schema_version": ("l9.pack-installation-record/v1"),
        "pack_id": pack_id,
        "pack_version": version,
        "archive_sha256": archive_hash,
        "manifest_sha256": "c" * 64,
        "signer_key_id": "key_" + "d" * 64,
        "compatibility_state": "compatible",
        "installed_at": "2026-07-18T00:00:00Z",
        "content_hashes": {},
        "limitations": [],
    }
    for name, value in {
        "manifest.json": {},
        "defense-pack.json": defense_pack,
        "compatibility.json": {},
        "checksums.json": {},
        "installation.json": installation,
    }.items():
        (root / name).write_text(
            json.dumps(value),
            encoding="utf-8",
        )
    (root / "archive.sha256").write_text(
        archive_hash + "\n",
        encoding="ascii",
    )


def test_activation_retains_previous_known_good(
    tmp_path: Path,
) -> None:
    paths = StatePaths(tmp_path / "state")
    paths.initialize()
    first = "pack_" + "1" * 64
    second = "pack_" + "2" * 64
    create_installed_pack(
        paths,
        pack_id=first,
        version="1.0.0",
        archive_hash="a" * 64,
    )
    create_installed_pack(
        paths,
        pack_id=second,
        version="2.0.0",
        archive_hash="b" * 64,
    )
    manager = ActivationManager(
        paths=paths,
        schema_root=ROOT / "schemas/lsp",
    )
    manager.activate(first)
    manager.activate(second)
    assert manager.load_active().pack_id == second
    assert manager.load_previous().pack_id == first


def test_rollback_reactivates_previous_pack(
    tmp_path: Path,
) -> None:
    paths = StatePaths(tmp_path / "state")
    paths.initialize()
    first = "pack_" + "1" * 64
    second = "pack_" + "2" * 64
    create_installed_pack(
        paths,
        pack_id=first,
        version="1.0.0",
        archive_hash="a" * 64,
    )
    create_installed_pack(
        paths,
        pack_id=second,
        version="2.0.0",
        archive_hash="b" * 64,
    )
    manager = ActivationManager(
        paths=paths,
        schema_root=ROOT / "schemas/lsp",
    )
    manager.activate(first)
    manager.activate(second)
    result = manager.rollback()
    assert result.pack_id == first
    assert manager.load_active().pack_id == first
    assert manager.load_previous().pack_id == second
