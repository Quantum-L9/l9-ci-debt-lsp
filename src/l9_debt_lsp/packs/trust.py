from __future__ import annotations
import base64
import datetime as dt
from pathlib import Path
from typing import Any
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
)
from l9_debt_lsp.contracts.schema import SchemaValidator
from .errors import TrustError
from .hashing import namespaced_hash
from .jsonio import load_json
from .models import TrustedKey
from .time import parse_utc, utc_now
KEY_USAGE = "defense-pack-verification"
def public_key_id(public_key_base64: str) -> str:
    try:
        raw = base64.b64decode(
            public_key_base64.encode("ascii"),
            validate=True,
        )
    except Exception as error:
        raise TrustError("public key is not valid base64") from error
    if len(raw) != 32:
        raise TrustError("Ed25519 public key must be 32 bytes")
    return namespaced_hash("key_", {"raw_public_key": raw.hex()})
class TrustRegistry:
    def __init__(
        self,
        registry_path: Path,
        schema_path: Path,
    ) -> None:
        self.registry_path = registry_path
        self.schema_path = schema_path
    def load(self) -> dict[str, TrustedKey]:
        if not self.registry_path.is_file():
            raise TrustError(
                f"trusted key registry does not exist: "
                f"{self.registry_path}"
            )
        document = load_json(self.registry_path)
        SchemaValidator(self.schema_path).validate(document)
        keys: dict[str, TrustedKey] = {}
        for entry in document["keys"]:
            key = TrustedKey(
                key_id=entry["key_id"],
                algorithm=entry["algorithm"],
                public_key=entry["public_key"],
                enabled=entry["enabled"],
                usages=tuple(sorted(entry["usages"])),
                issuer=entry["issuer"],
                not_before=entry.get("not_before"),
                not_after=entry.get("not_after"),
                limitations=tuple(
                    sorted(set(entry.get("limitations", [])))
                ),
            )
            calculated = public_key_id(key.public_key)
            if key.key_id != calculated:
                raise TrustError(
                    f"trusted key identity mismatch: {key.key_id}"
                )
            if key.key_id in keys:
                raise TrustError(
                    f"duplicate trusted key identity: {key.key_id}"
                )
            keys[key.key_id] = key
        return keys
    def require_verification_key(
        self,
        *,
        key_id: str,
        embedded_public_key: str,
        now: dt.datetime | None = None,
    ) -> TrustedKey:
        now = now or utc_now()
        keys = self.load()
        key = keys.get(key_id)
        if key is None:
            raise TrustError(f"unknown signer key: {key_id}")
        if not key.enabled:
            raise TrustError(f"signer key is disabled: {key_id}")
        if key.algorithm != "Ed25519":
            raise TrustError(
                f"unsupported signer algorithm: {key.algorithm}"
            )
        if KEY_USAGE not in key.usages:
            raise TrustError(
                f"signer key lacks required usage: {KEY_USAGE}"
            )
        if key.public_key != embedded_public_key:
            raise TrustError(
                "manifest public key does not match trusted key"
            )
        if key.not_before is not None:
            if now < parse_utc(key.not_before):
                raise TrustError(
                    f"signer key is not yet valid: {key_id}"
                )
        if key.not_after is not None:
            if now >= parse_utc(key.not_after):
                raise TrustError(
                    f"signer key has expired: {key_id}"
                )
        try:
            raw = base64.b64decode(
                key.public_key.encode("ascii"),
                validate=True,
            )
            Ed25519PublicKey.from_public_bytes(raw)
        except Exception as error:
            raise TrustError(
                f"trusted key is not valid Ed25519: {key_id}"
            ) from error
        return key
