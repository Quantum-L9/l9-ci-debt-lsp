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
    missing = [name for name in REQUIRED_MEMBERS if not (root / name).is_file()]
    if missing:
        raise ArchiveIntegrityError(f"required archive members are missing: {missing}")


#: The `checksums.json` archive member, published by the producer as
#: `schemas/intelligence/defense-checksums.schema.json` in
#: `l9-ci-debt-intelligence`, whose `.l9/publication-contract.yaml` gives it
#: `owner: intelligence` under `authority.intelligence: assemble pack`.
CHECKSUMS_PROTOCOL = "l9.defense-checksums/v1"

_SHA256_CHARACTERS = frozenset("0123456789abcdef")
_SHA256_LENGTH = 64


def load_checksums(root: Path) -> dict[str, str]:
    """Read and validate `checksums.json` against the published shape.

    This used to read `document.get("checksums", document)` -- a shape that
    belongs to a *different* document: the bare `checksums` mapping inside
    `defense-pack.json`. Applied to this member the fallback landed on the
    envelope itself, so the first key it met was `files`, whose value is an
    object, and every real pack was refused with `checksum value must be a
    string: files` at verification step `validate_checksums_document`.

    Nothing caught it because every fixture wrote `checksums.json` as `{}`,
    which satisfied the old loader trivially and left `verify_member_checksums`
    with nothing to verify -- a vacuous pass at step 13 as well as a wrong
    shape at step 12.

    The guess is gone deliberately. A bare mapping carries no version, so a
    consumer that accepts one cannot tell a format change from a valid
    document, which is how this divergence survived. `schema_version` is now
    required and matched exactly.
    """
    document = load_json(root / "checksums.json")
    version = document.get("schema_version")
    if version != CHECKSUMS_PROTOCOL:
        raise ArchiveIntegrityError(
            f"checksums document must declare {CHECKSUMS_PROTOCOL!r}, found {version!r}"
        )
    unknown = sorted(set(document) - {"schema_version", "files"})
    if unknown:
        raise ArchiveIntegrityError(f"checksums document has unknown fields: {unknown}")
    checksums = document.get("files")
    if not isinstance(checksums, dict):
        raise ArchiveIntegrityError("checksums document 'files' must be an object")
    result: dict[str, str] = {}
    for name, digest in checksums.items():
        if not isinstance(name, str):
            raise ArchiveIntegrityError("checksum path must be a string")
        if not isinstance(digest, str):
            raise ArchiveIntegrityError(f"checksum value must be a string: {name}")
        if len(digest) != _SHA256_LENGTH or not _SHA256_CHARACTERS.issuperset(digest):
            raise ArchiveIntegrityError(f"checksum must be SHA-256: {name}")
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
            raise ArchiveIntegrityError(f"unsafe checksum path: {relative_name}")
        path = root / relative
        if not path.is_file():
            raise ArchiveIntegrityError(
                f"checksummed member is missing: {relative_name}"
            )
        actual = sha256_file(path)
        if actual != expected:
            raise ArchiveIntegrityError(f"member checksum mismatch: {relative_name}")
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
        raise PackValidationError("manifest and defense pack use different pack IDs")
    if manifest["pack_version"] != defense_pack["version"]:
        raise PackValidationError("manifest and defense pack use different versions")
    compatibility = (
        load_json(
            Path(
                defense_pack.get(
                    "__compatibility_path__",
                    "compatibility.json",
                )
            )
        )
        if False
        else None
    )
    del compatibility
