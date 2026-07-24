from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO

from l9_debt_lsp.contracts.canonical import canonical_json


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        _update_digest(stream, digest)
    return digest.hexdigest()


def _update_digest(
    stream: BinaryIO,
    digest: hashlib._Hash,
) -> None:
    while True:
        block = stream.read(1024 * 1024)
        if not block:
            return
        digest.update(block)


def namespaced_hash(prefix: str, value: object) -> str:
    return prefix + sha256_bytes(canonical_json(value))
