from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

from l9_debt_lsp.packs.hashing import namespaced_hash


def normalized_uri(uri: str) -> str:
    parts = urlsplit(uri)
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path,
            parts.query,
            "",
        )
    )


def workspace_identity(workspace_uri: str) -> str:
    return namespaced_hash(
        "workspace_",
        {
            "normalized_uri": normalized_uri(workspace_uri),
        },
    )


def document_identity(uri: str) -> str:
    return namespaced_hash(
        "doc_",
        {
            "normalized_uri": normalized_uri(uri),
        },
    )


def request_identity(
    *,
    workspace_id: str,
    workspace_generation: int,
    document_id: str,
    document_version: int,
    active_pack_id: str,
) -> str:
    return namespaced_hash(
        "request_",
        {
            "workspace_id": workspace_id,
            "workspace_generation": workspace_generation,
            "document_id": document_id,
            "document_version": document_version,
            "active_pack_id": active_pack_id,
        },
    )
