from __future__ import annotations

from l9_debt_lsp.diagnostics.sanitization import (
    sanitize_message,
)


def test_absolute_paths_are_redacted() -> None:
    message = sanitize_message("Failure in /home/alice/private/project/file.py")
    assert "/home/alice" not in message
    assert "<redacted-path>" in message


def test_tokens_are_redacted() -> None:
    message = sanitize_message("Authorization: Bearer abcdefghijklmnopqrstuvwxyz")
    assert "abcdefghijklmnopqrstuvwxyz" not in message
    assert "<redacted-secret>" in message
