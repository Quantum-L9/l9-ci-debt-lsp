from __future__ import annotations

import json
import re
from typing import Any

from .errors import TelemetryPrivacyError

MAX_EVENT_BYTES = 16 * 1024
PROHIBITED_KEYS = {
    "source_content",
    "source_snippet",
    "document_text",
    "replacement_text",
    "preview_diff",
    "diagnostic_message",
    "evidence_summary",
    "related_information_message",
    "absolute_path",
    "relative_path",
    "document_uri",
    "workspace_uri",
    "repository_name",
    "repository_url",
    "repository_remote",
    "branch_name",
    "commit_sha",
    "developer_name",
    "developer_email",
    "account_id",
    "machine_hostname",
    "machine_serial",
    "ip_address",
    "secret_value",
    "access_token",
    "raw_log",
    "raw_exception",
    "raw_corpus_record",
    "repository_graph",
}
PROHIBITED_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9_.-])/(?:home|Users|private|tmp|var|opt)/\S+"),
    re.compile(r"(?<![A-Za-z0-9_.-])[A-Za-z]:\\[^\s]+"),
    re.compile(r"\bfile://\S+"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(
        r"(?i)\b(?:password|passwd|secret|token|api[_-]?key)"
        r"\s*[:=]\s*\S+"
    ),
)


def validate_privacy(value: Any) -> None:
    _validate_structure(value)
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(encoded) > MAX_EVENT_BYTES:
        raise TelemetryPrivacyError("telemetry event exceeds maximum byte size")
    text = encoded.decode("utf-8")
    for pattern in PROHIBITED_PATTERNS:
        if pattern.search(text):
            raise TelemetryPrivacyError(
                "telemetry event contains prohibited value pattern"
            )


def _validate_structure(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).casefold()
            if normalized in PROHIBITED_KEYS:
                raise TelemetryPrivacyError(f"telemetry field is prohibited: {key}")
            _validate_structure(item)
    elif isinstance(value, list):
        for item in value:
            _validate_structure(item)
    elif isinstance(value, tuple):
        for item in value:
            _validate_structure(item)
