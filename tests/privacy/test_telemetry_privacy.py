from __future__ import annotations

import pytest

from l9_debt_lsp.telemetry.errors import (
    TelemetryPrivacyError,
)
from l9_debt_lsp.telemetry.privacy import (
    validate_privacy,
)


@pytest.mark.parametrize(
    "document",
    [
        {"source_content": "print('secret')"},
        {"document_uri": "file:///home/alice/project/a.py"},
        {"value": "/home/alice/project/a.py"},
        {"value": "alice@example.com"},
        {"value": "Bearer abcdefghijklmnopqrstuvwxyz"},
        {"value": "ghp_abcdefghijklmnopqrstuvwxyz123456"},
        {"value": "password=supersecret"},
    ],
)
def test_prohibited_telemetry_is_rejected(
    document: dict[str, str],
) -> None:
    with pytest.raises(TelemetryPrivacyError):
        validate_privacy(document)


def test_canonical_identifiers_are_allowed() -> None:
    validate_privacy(
        {
            "canonical_rule_id": "l9.example",
            "finding_id": "finding-123",
            "rule_pack_id": "pack_" + "a" * 64,
        }
    )
