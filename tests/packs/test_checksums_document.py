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

    def test_an_empty_files_mapping_is_refused(self, tmp_path: Path) -> None:
        """The vacuous document, in the shape the envelope makes valid.

        Every other rule here is satisfied -- exact version, no unknown
        fields, `files` an object of the right type -- so this is the document
        that reaches a consumer looking correct and verifies nothing. It is
        also precisely what the old fixtures wrote, which is how a defect
        refusing 100% of real packs went unnoticed.
        """
        root = write(tmp_path, {"schema_version": CHECKSUMS_PROTOCOL, "files": {}})
        with pytest.raises(ArchiveIntegrityError, match="names no members"):
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


def member(root: Path, name: str, payload: bytes) -> str:
    """Write an archive member and return its real digest."""
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return sha256_file(path)


class TestEveryMemberMustBeChecksummed:
    """Coverage, the half of step 13 that was missing.

    Verifying the entries you are handed answers "does everything named here
    match?" and never "is everything here named?". An archive member the
    document omits is one nobody hashes, so it passes step 13 untouched. These
    pin the equality: checksummed set == content members, less `checksums.json`.
    """

    def test_a_member_with_no_checksum_entry_is_refused(self, tmp_path: Path) -> None:
        """The core case: a real file the document simply does not mention."""
        digest = member(tmp_path, "defense-pack.json", b'{"a":1}\n')
        member(tmp_path, "compatibility.json", b'{"b":2}\n')
        with pytest.raises(ArchiveIntegrityError, match="no checksum entry"):
            verify_member_checksums(tmp_path, {"defense-pack.json": digest})

    def test_an_unlisted_nested_content_member_is_refused(self, tmp_path: Path) -> None:
        """`rules/` content is where an unlisted member would actually hide."""
        digest = member(tmp_path, "defense-pack.json", b'{"a":1}\n')
        member(tmp_path, "rules/injected.json", b'{"malicious":true}\n')
        with pytest.raises(ArchiveIntegrityError, match=r"rules/injected\.json"):
            verify_member_checksums(tmp_path, {"defense-pack.json": digest})

    def test_the_error_names_every_uncovered_member(self, tmp_path: Path) -> None:
        digest = member(tmp_path, "defense-pack.json", b'{"a":1}\n')
        member(tmp_path, "compatibility.json", b'{"b":2}\n')
        member(tmp_path, "rules/extra.json", b"{}\n")
        with pytest.raises(ArchiveIntegrityError) as raised:
            verify_member_checksums(tmp_path, {"defense-pack.json": digest})
        assert "compatibility.json" in str(raised.value)
        assert "rules/extra.json" in str(raised.value)

    def test_full_coverage_verifies(self, tmp_path: Path) -> None:
        """The real shape: every content member named, and it passes."""
        checksums = {
            "defense-pack.json": member(tmp_path, "defense-pack.json", b'{"a":1}\n'),
            "compatibility.json": member(tmp_path, "compatibility.json", b'{"b":2}\n'),
            "rules/one.json": member(tmp_path, "rules/one.json", b'{"c":3}\n'),
        }
        (tmp_path / "checksums.json").write_text("{}", encoding="utf-8")
        assert verify_member_checksums(tmp_path, checksums) == checksums

    def test_the_checksums_document_itself_needs_no_entry(self, tmp_path: Path) -> None:
        """It cannot carry its own digest: writing it changes the bytes.

        The one exclusion. Requiring it would refuse every real pack, which is
        the failure mode this whole PR exists to fix -- so it is pinned rather
        than left as a comment.
        """
        digest = member(tmp_path, "defense-pack.json", b'{"a":1}\n')
        (tmp_path / "checksums.json").write_text("{}", encoding="utf-8")
        assert verify_member_checksums(tmp_path, {"defense-pack.json": digest}) == {
            "defense-pack.json": digest
        }

    def test_an_empty_directory_is_not_a_member(self, tmp_path: Path) -> None:
        """Directories carry no content, so they need no digest."""
        digest = member(tmp_path, "defense-pack.json", b'{"a":1}\n')
        (tmp_path / "rules").mkdir()
        assert verify_member_checksums(tmp_path, {"defense-pack.json": digest}) == {
            "defense-pack.json": digest
        }

    def test_a_missing_member_still_reports_that_and_not_coverage(
        self, tmp_path: Path
    ) -> None:
        """Ordering guard.

        Coverage runs after the per-entry loop on purpose. Were it first, an
        entry naming an absent file would be recast as a coverage complaint
        and the specific fault would be lost.
        """
        with pytest.raises(ArchiveIntegrityError, match="member is missing"):
            verify_member_checksums(tmp_path, {"absent.json": DIGEST})
