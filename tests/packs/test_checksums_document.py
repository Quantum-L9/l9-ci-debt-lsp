"""`checksums.json` is the producer's document, and we were reading another.

`load_checksums` used to start with

    checksums = document.get("checksums", document)

which is the shape of the bare `checksums` mapping inside
`defense-pack.json`. `checksums.json` is a different document: the producer
(`l9-ci-debt-intelligence`, which owns `assemble pack`) has always written an
envelope, `{"schema_version": "l9.defense-checksums/v1", "files": {...}}`. The
fallback therefore landed on the envelope itself, met `files` first because
canonical JSON sorts keys, found an object where a digest belonged, and refused
every real pack at verification step 12:

    ArchiveIntegrityError: checksum value must be a string: files

Neither of these functions had a single test. The three fixtures that write a
`checksums.json` all write `{}` -- and `{}` satisfied the old loader trivially,
so step 12 passed on nothing and step 13 verified nothing. That is why a defect
that refuses 100% of real packs survived: the suite only ever fed it documents
with no content.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from l9_debt_lsp.packs.contents import (
    CHECKSUMS_PROTOCOL,
    load_checksums,
    verify_member_checksums,
)
from l9_debt_lsp.packs.errors import ArchiveIntegrityError
from l9_debt_lsp.packs.hashing import sha256_file

DIGEST = "a" * 64


def write(root: Path, document: object) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "checksums.json").write_text(json.dumps(document), encoding="utf-8")
    return root


def test_the_exact_condition_that_refused_every_real_pack(tmp_path: Path) -> None:
    """The producer's real document must load, not raise.

    This is the regression: the structural condition is an object at `files`,
    which is precisely what the old loader reported as a non-string checksum.
    """
    root = write(
        tmp_path,
        {
            "schema_version": CHECKSUMS_PROTOCOL,
            "files": {"defense-pack.json": DIGEST, "compatibility.json": DIGEST},
        },
    )
    assert load_checksums(root) == {
        "compatibility.json": DIGEST,
        "defense-pack.json": DIGEST,
    }


def test_the_old_failure_message_can_no_longer_be_produced_by_the_envelope(
    tmp_path: Path,
) -> None:
    """`files` must never again be read as if it were a digest."""
    root = write(
        tmp_path,
        {"schema_version": CHECKSUMS_PROTOCOL, "files": {"a.json": DIGEST}},
    )
    try:
        load_checksums(root)
    except ArchiveIntegrityError as error:  # pragma: no cover - regression guard
        pytest.fail(f"the envelope was rejected again: {error}")


def test_entries_are_returned_sorted(tmp_path: Path) -> None:
    root = write(
        tmp_path,
        {
            "schema_version": CHECKSUMS_PROTOCOL,
            "files": {"z.json": DIGEST, "a.json": DIGEST},
        },
    )
    assert list(load_checksums(root)) == ["a.json", "z.json"]


class TestItRefusesRatherThanGuessing:
    """The fallback is gone on purpose; these pin that it stays gone."""

    def test_a_bare_path_to_digest_mapping_is_refused(self, tmp_path: Path) -> None:
        """What the old loader silently accepted. It carries no version."""
        root = write(tmp_path, {"defense-pack.json": DIGEST})
        with pytest.raises(ArchiveIntegrityError, match="must declare"):
            load_checksums(root)

    def test_the_packs_inline_checksums_field_is_refused(self, tmp_path: Path) -> None:
        """The shape this loader was mistakenly written for."""
        root = write(tmp_path, {"checksums": {"defense-pack.json": DIGEST}})
        with pytest.raises(ArchiveIntegrityError, match="must declare"):
            load_checksums(root)

    def test_an_empty_document_is_refused(self, tmp_path: Path) -> None:
        """`{}` is what made every existing fixture vacuous."""
        root = write(tmp_path, {})
        with pytest.raises(ArchiveIntegrityError, match="must declare"):
            load_checksums(root)

    def test_a_future_schema_version_is_refused(self, tmp_path: Path) -> None:
        root = write(
            tmp_path,
            {"schema_version": "l9.defense-checksums/v2", "files": {}},
        )
        with pytest.raises(ArchiveIntegrityError, match="must declare"):
            load_checksums(root)

    def test_an_unknown_top_level_field_is_refused(self, tmp_path: Path) -> None:
        root = write(
            tmp_path,
            {"schema_version": CHECKSUMS_PROTOCOL, "files": {}, "extra": 1},
        )
        with pytest.raises(ArchiveIntegrityError, match="unknown fields"):
            load_checksums(root)

    def test_a_non_object_files_value_is_refused(self, tmp_path: Path) -> None:
        root = write(tmp_path, {"schema_version": CHECKSUMS_PROTOCOL, "files": []})
        with pytest.raises(ArchiveIntegrityError, match="'files' must be an object"):
            load_checksums(root)

    def test_a_missing_files_field_is_refused(self, tmp_path: Path) -> None:
        root = write(tmp_path, {"schema_version": CHECKSUMS_PROTOCOL})
        with pytest.raises(ArchiveIntegrityError, match="'files' must be an object"):
            load_checksums(root)

    def test_a_nested_object_digest_is_refused(self, tmp_path: Path) -> None:
        root = write(
            tmp_path,
            {
                "schema_version": CHECKSUMS_PROTOCOL,
                "files": {"a.json": {"sha": DIGEST}},
            },
        )
        with pytest.raises(ArchiveIntegrityError, match=r"must be a string: a\.json"):
            load_checksums(root)

    def test_a_short_digest_is_refused(self, tmp_path: Path) -> None:
        root = write(
            tmp_path,
            {"schema_version": CHECKSUMS_PROTOCOL, "files": {"a.json": "a" * 63}},
        )
        with pytest.raises(ArchiveIntegrityError, match="must be SHA-256"):
            load_checksums(root)

    def test_a_non_hex_digest_of_the_right_length_is_refused(
        self, tmp_path: Path
    ) -> None:
        """Length alone was the old check; 64 'z' characters passed it."""
        root = write(
            tmp_path,
            {"schema_version": CHECKSUMS_PROTOCOL, "files": {"a.json": "z" * 64}},
        )
        with pytest.raises(ArchiveIntegrityError, match="must be SHA-256"):
            load_checksums(root)

    def test_an_uppercase_digest_is_refused(self, tmp_path: Path) -> None:
        """Canonical output is lowercase; accepting both makes two identities."""
        root = write(
            tmp_path,
            {"schema_version": CHECKSUMS_PROTOCOL, "files": {"a.json": "A" * 64}},
        )
        with pytest.raises(ArchiveIntegrityError, match="must be SHA-256"):
            load_checksums(root)


class TestMemberVerificationActuallyRuns:
    """Step 13 had never verified a member; these make it do so."""

    def test_a_matching_member_verifies(self, tmp_path: Path) -> None:
        (tmp_path / "defense-pack.json").write_bytes(b'{"a":1}\n')
        digest = sha256_file(tmp_path / "defense-pack.json")
        verified = verify_member_checksums(tmp_path, {"defense-pack.json": digest})
        assert verified == {"defense-pack.json": digest}

    def test_a_tampered_member_is_refused(self, tmp_path: Path) -> None:
        (tmp_path / "defense-pack.json").write_bytes(b'{"a":1}\n')
        digest = sha256_file(tmp_path / "defense-pack.json")
        (tmp_path / "defense-pack.json").write_bytes(b'{"a":2}\n')
        with pytest.raises(ArchiveIntegrityError, match="member checksum mismatch"):
            verify_member_checksums(tmp_path, {"defense-pack.json": digest})

    def test_a_missing_member_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(ArchiveIntegrityError, match="member is missing"):
            verify_member_checksums(tmp_path, {"absent.json": DIGEST})

    def test_a_traversing_member_path_is_refused(self, tmp_path: Path) -> None:
        for name in ("../escape.json", "rules/../../escape.json"):
            with pytest.raises(ArchiveIntegrityError, match="unsafe checksum path"):
                verify_member_checksums(tmp_path, {name: DIGEST})
