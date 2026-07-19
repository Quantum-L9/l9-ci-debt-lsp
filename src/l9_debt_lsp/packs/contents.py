from __future__ import annotations
from pathlib import Path
from typing import Any
from l9_debt_lsp.contracts.schema import SchemaValidator
from .errors import ArchiveIntegrityError, PackValidationError
from .hashing import sha256_file
from .jsonio import load_json
REQUIRED_MEMBERS = (
    "defense-pack.json",
    "compatibility.json",
    "checksums.json",
)
def validate_required_members(root: Path) -> None:
    missing = [
        name for name in REQUIRED_MEMBERS
        if not (root / name).is_file()
    ]
    if missing:
        raise ArchiveIntegrityError(
            f"required archive members are missing: {missing}"
        )
def load_checksums(root: Path) -> dict[str, str]:
    document = load_json(root / "checksums.json")
    checksums = document.get("checksums", document)
    if not isinstance(checksums, dict):
        raise ArchiveIntegrityError(
            "checksums document must contain an object"
        )
    result: dict[str, str] = {}
    for name, digest in checksums.items():
        if not isinstance(name, str):
            raise ArchiveIntegrityError(
                "checksum path must be a string"
            )
        if not isinstance(digest, str):
            raise ArchiveIntegrityError(
                f"checksum value must be a string: {name}"
            )
        if len(digest) != 64:
            raise ArchiveIntegrityError(
                f"checksum must be SHA-256: {name}"
            )
        result[name] = digest
    return dict(sorted(result.items()))
def verify_member_checksums(
    root: Path,
    checksums: dict[str, str],
) -> dict[str, str]:
    verified: dict[str, str] = {}
    for relative_name, expected in checksums.items():
        relative = Path(relative_name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ArchiveIntegrityError(
                f"unsafe checksum path: {relative_name}"
            )
        path = root / relative
        if not path.is_file():
            raise ArchiveIntegrityError(
                f"checksummed member is missing: {relative_name}"
            )
        actual = sha256_file(path)
        if actual != expected:
            raise ArchiveIntegrityError(
                f"member checksum mismatch: {relative_name}"
            )
        verified[relative_name] = actual
    return verified
def load_and_validate_defense_pack(
    *,
    root: Path,
    schema_path: Path,
) -> dict[str, Any]:
    defense_pack = load_json(root / "defense-pack.json")
    try:
        SchemaValidator(schema_path).validate(defense_pack)
    except Exception as error:
        raise PackValidationError(
            f"defense-pack schema validation failed: {error}"
        ) from error
    return defense_pack
def validate_identity_consistency(
    *,
    manifest: dict[str, Any],
    defense_pack: dict[str, Any],
) -> None:
    if manifest["pack_id"] != defense_pack["pack_id"]:
        raise PackValidationError(
            "manifest and defense pack use different pack IDs"
        )
    if manifest["pack_version"] != defense_pack["version"]:
        raise PackValidationError(
            "manifest and defense pack use different versions"
        )
    compatibility = load_json(
        Path(defense_pack.get(
            "__compatibility_path__",
            "compatibility.json",
        ))
    ) if False else None
    del compatibility
