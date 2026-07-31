from __future__ import annotations

import io
import tarfile
from pathlib import Path

import pytest

from l9_debt_lsp.packs.archive import (
    extract_archive_safely,
    inspect_archive,
)
from l9_debt_lsp.packs.errors import ArchiveSecurityError


def create_archive(
    path: Path,
    members: dict[str, bytes],
) -> None:
    with tarfile.open(path, "w:gz") as archive:
        for name, content in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))


def test_rejects_parent_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.tar.gz"
    create_archive(archive, {"../escape.txt": b"escape"})
    with pytest.raises(ArchiveSecurityError):
        inspect_archive(archive)


def test_rejects_absolute_path(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.tar.gz"
    create_archive(archive, {"/tmp/escape.txt": b"escape"})
    with pytest.raises(ArchiveSecurityError):
        inspect_archive(archive)


def test_rejects_case_folded_duplicate_paths(
    tmp_path: Path,
) -> None:
    archive = tmp_path / "unsafe.tar.gz"
    create_archive(
        archive,
        {
            "rules/Rule.yaml": b"one",
            "rules/rule.yaml": b"two",
        },
    )
    with pytest.raises(ArchiveSecurityError):
        inspect_archive(archive)


def test_safe_archive_is_extracted(tmp_path: Path) -> None:
    archive = tmp_path / "safe.tar.gz"
    destination = tmp_path / "out"
    create_archive(
        archive,
        {
            "defense-pack.json": b"{}",
            "compatibility.json": b"{}",
            "checksums.json": b"{}",
            "rules/example.yaml": b"id: example\n",
        },
    )
    result = extract_archive_safely(
        archive,
        destination,
    )
    assert result.member_count == 4
    assert (destination / "rules/example.yaml").read_bytes() == b"id: example\n"
