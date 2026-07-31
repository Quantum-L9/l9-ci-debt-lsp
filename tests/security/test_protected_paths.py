from __future__ import annotations

import pytest

from l9_debt_lsp.actions.errors import ProtectedPathError
from l9_debt_lsp.actions.protected_paths import (
    require_editable_path,
)


@pytest.mark.parametrize(
    "uri",
    [
        "file:///workspace/.env",
        "file:///workspace/.git/config",
        "file:///workspace/.github/workflows/ci.yml",
        "file:///workspace/state/trust/keys.json",
        "file:///workspace/private.pem",
    ],
)
def test_protected_paths_are_rejected(uri: str) -> None:
    with pytest.raises(ProtectedPathError):
        require_editable_path(
            document_uri=uri,
            workspace_uri="file:///workspace",
        )


def test_normal_source_file_is_allowed() -> None:
    result = require_editable_path(
        document_uri="file:///workspace/src/example.py",
        workspace_uri="file:///workspace",
    )
    assert result == "src/example.py"
