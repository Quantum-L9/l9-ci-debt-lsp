from __future__ import annotations

import base64
import hashlib

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from l9_debt_lsp.packs.errors import SignatureError
from l9_debt_lsp.packs.signature import (
    verify_archive_digest,
)


def test_valid_signature_is_accepted() -> None:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    digest = hashlib.sha256(b"archive").hexdigest()
    signature = private.sign(bytes.fromhex(digest))
    verify_archive_digest(
        archive_sha256=digest,
        signature_base64=base64.b64encode(signature).decode("ascii"),
        public_key_base64=base64.b64encode(public).decode("ascii"),
    )


def test_modified_digest_is_rejected() -> None:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    digest = hashlib.sha256(b"archive").hexdigest()
    signature = private.sign(bytes.fromhex(digest))
    modified = hashlib.sha256(b"modified").hexdigest()
    with pytest.raises(SignatureError):
        verify_archive_digest(
            archive_sha256=modified,
            signature_base64=base64.b64encode(signature).decode("ascii"),
            public_key_base64=base64.b64encode(public).decode("ascii"),
        )
