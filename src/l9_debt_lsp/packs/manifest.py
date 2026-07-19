from __future__ import annotations
from pathlib import Path
from typing import Any
from l9_debt_lsp.contracts.schema import SchemaValidator
from .errors import ManifestValidationError
from .hashing import sha256_file
from .jsonio import load_json
def load_and_validate_manifest(
    *,
    manifest_path: Path,
    schema_path: Path,
) -> dict[str, Any]:
    try:
        manifest = load_json(manifest_path)
        SchemaValidator(schema_path).validate(manifest)
    except Exception as error:
        raise ManifestValidationError(
            f"publication manifest validation failed: {error}"
        ) from error
    if manifest["signature_algorithm"] != "Ed25519":
        raise ManifestValidationError(
            "only Ed25519 signatures are supported"
        )
    if not all(manifest["publication_gates"].values()):
        raise ManifestValidationError(
            "publication manifest contains an unpassed gate"
        )
    return manifest
def verify_archive_reference(
    *,
    manifest: dict[str, Any],
    archive_path: Path,
) -> str:
    actual_size = archive_path.stat().st_size
    if actual_size != manifest["archive_size"]:
        raise ManifestValidationError(
            "archive size does not match publication manifest"
        )
    actual_hash = sha256_file(archive_path)
    if actual_hash != manifest["archive_sha256"]:
        raise ManifestValidationError(
            "archive SHA-256 does not match publication manifest"
        )
    return actual_hash
