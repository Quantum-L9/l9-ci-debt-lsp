from __future__ import annotations
import base64
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
)
from .errors import SignatureError
def verify_archive_digest(
    *,
    archive_sha256: str,
    signature_base64: str,
    public_key_base64: str,
) -> None:
    try:
        digest = bytes.fromhex(archive_sha256)
    except ValueError as error:
        raise SignatureError(
            "archive digest is not valid hexadecimal"
        ) from error
    try:
        signature = base64.b64decode(
            signature_base64.encode("ascii"),
            validate=True,
        )
        public_key = base64.b64decode(
            public_key_base64.encode("ascii"),
            validate=True,
        )
    except Exception as error:
        raise SignatureError(
            "signature or public key is not valid base64"
        ) from error
    if len(public_key) != 32:
        raise SignatureError(
            "Ed25519 public key must be 32 bytes"
        )
    try:
        Ed25519PublicKey.from_public_bytes(
            public_key
        ).verify(signature, digest)
    except InvalidSignature as error:
        raise SignatureError(
            "defense-pack signature verification failed"
        ) from error
    except Exception as error:
        raise SignatureError(
            "unable to verify defense-pack signature"
        ) from error
