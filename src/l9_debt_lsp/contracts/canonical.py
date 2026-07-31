from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> bytes:
    """Serialize a JSON-compatible value deterministically."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_document(value: Any) -> str:
    """Return the SHA-256 hash of canonical JSON."""
    return hashlib.sha256(canonical_json(value)).hexdigest()
