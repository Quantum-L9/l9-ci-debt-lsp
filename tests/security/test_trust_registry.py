from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from l9_debt_lsp.packs.errors import TrustError
from l9_debt_lsp.packs.trust import (
    TrustRegistry,
    public_key_id,
)

ROOT = Path(__file__).resolve().parents[2]


def public_key() -> str:
    private = Ed25519PrivateKey.generate()
    raw = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(raw).decode("ascii")


def write_registry(
    path: Path,
    key: str,
    *,
    enabled: bool,
) -> str:
    key_id = public_key_id(key)
    path.write_text(
        json.dumps(
            {
                "schema_version": ("l9.trusted-key-registry/v1"),
                "keys": [
                    {
                        "key_id": key_id,
                        "algorithm": "Ed25519",
                        "public_key": key,
                        "enabled": enabled,
                        "usages": ["defense-pack-verification"],
                        "issuer": "test",
                        "not_before": None,
                        "not_after": None,
                        "limitations": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return key_id


def test_enabled_key_is_accepted(tmp_path: Path) -> None:
    registry_path = tmp_path / "keys.json"
    key = public_key()
    key_id = write_registry(
        registry_path,
        key,
        enabled=True,
    )
    registry = TrustRegistry(
        registry_path,
        ROOT / "schemas/lsp/trusted-key-registry.schema.json",
    )
    result = registry.require_verification_key(
        key_id=key_id,
        embedded_public_key=key,
    )
    assert result.key_id == key_id


def test_disabled_key_is_rejected(tmp_path: Path) -> None:
    registry_path = tmp_path / "keys.json"
    key = public_key()
    key_id = write_registry(
        registry_path,
        key,
        enabled=False,
    )
    registry = TrustRegistry(
        registry_path,
        ROOT / "schemas/lsp/trusted-key-registry.schema.json",
    )
    with pytest.raises(TrustError):
        registry.require_verification_key(
            key_id=key_id,
            embedded_public_key=key,
        )
