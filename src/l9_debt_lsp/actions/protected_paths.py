from __future__ import annotations

from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit

from .errors import ProtectedPathError

PROTECTED_EXACT = {
    ".git",
    ".env",
    ".npmrc",
    ".pypirc",
    "credentials.json",
}
PROTECTED_PREFIXES = (
    ".git/",
    ".github/workflows/",
    ".l9/trust/",
    ".l9-runtime/",
    "state/trust/",
    "state/activation/",
    "state/packs/",
    "state/retirement/",
    "state/quarantine/",
)
PROTECTED_SUFFIXES = (
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".crt",
    ".cer",
)


def normalized_workspace_path(
    *,
    document_uri: str,
    workspace_uri: str,
) -> str:
    document = urlsplit(document_uri)
    workspace = urlsplit(workspace_uri)
    if document.scheme != "file" or workspace.scheme != "file":
        raise ProtectedPathError("code actions require file-backed documents")
    document_path = PurePosixPath(unquote(document.path))
    workspace_path = PurePosixPath(unquote(workspace.path))
    try:
        relative = document_path.relative_to(workspace_path)
    except ValueError as error:
        raise ProtectedPathError("document is outside the workspace") from error
    value = relative.as_posix()
    if value in {"", "."}:
        raise ProtectedPathError("workspace root is not an editable document")
    return value


def require_editable_path(
    *,
    document_uri: str,
    workspace_uri: str,
) -> str:
    relative = normalized_workspace_path(
        document_uri=document_uri,
        workspace_uri=workspace_uri,
    )
    folded = relative.casefold()
    if folded in {value.casefold() for value in PROTECTED_EXACT}:
        raise ProtectedPathError(f"protected path: {relative}")
    if any(folded.startswith(prefix.casefold()) for prefix in PROTECTED_PREFIXES):
        raise ProtectedPathError(f"protected path: {relative}")
    if any(folded.endswith(suffix.casefold()) for suffix in PROTECTED_SUFFIXES):
        raise ProtectedPathError(f"protected credential path: {relative}")
    return relative
