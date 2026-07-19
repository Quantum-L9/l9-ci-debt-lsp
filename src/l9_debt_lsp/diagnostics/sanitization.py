from __future__ import annotations

import re

MAX_DIAGNOSTIC_MESSAGE = 2000
MAX_RELATED_MESSAGE = 1000
ABSOLUTE_PATH = re.compile(
    r"(?:"
    r"(?<![A-Za-z0-9_.-])/(?:home|Users|private|tmp|var|opt)/[^\s]+"
    r"|"
    r"(?<![A-Za-z0-9_.-])[A-Za-z]:\\[^\s]+"
    r")"
)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


def sanitize_message(
    value: str,
    *,
    maximum: int = MAX_DIAGNOSTIC_MESSAGE,
) -> str:
    result = value.replace("\x00", "")
    result = ABSOLUTE_PATH.sub("<redacted-path>", result)
    for pattern in SECRET_PATTERNS:
        result = pattern.sub("<redacted-secret>", result)
    result = " ".join(result.split())
    if not result:
        result = "L9 diagnostic details are unavailable."
    if len(result) > maximum:
        result = result[: maximum - 1] + "…"
    return result
