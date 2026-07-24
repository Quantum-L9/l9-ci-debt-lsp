from __future__ import annotations

import os
import shutil
import tarfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .errors import ArchiveSecurityError

MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024
MAX_MEMBER_COUNT = 10_000
MAX_SINGLE_MEMBER_BYTES = 50 * 1024 * 1024
MAX_PATH_LENGTH = 512
MAX_PATH_DEPTH = 20


@dataclass(frozen=True)
class ArchiveInspection:
    member_count: int
    uncompressed_bytes: int
    file_paths: tuple[str, ...]


def _validate_member_name(name: str) -> PurePosixPath:
    if not name:
        raise ArchiveSecurityError("archive contains an empty member name")
    if len(name) > MAX_PATH_LENGTH:
        raise ArchiveSecurityError(f"archive member path exceeds limit: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute():
        raise ArchiveSecurityError(f"absolute archive path is prohibited: {name!r}")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ArchiveSecurityError(f"unsafe archive member path: {name!r}")
    if len(path.parts) > MAX_PATH_DEPTH:
        raise ArchiveSecurityError(f"archive path depth exceeds limit: {name!r}")
    return path


def inspect_archive(path: Path) -> ArchiveInspection:
    archive_size = path.stat().st_size
    if archive_size > MAX_ARCHIVE_BYTES:
        raise ArchiveSecurityError(f"archive exceeds {MAX_ARCHIVE_BYTES} bytes")
    member_count = 0
    uncompressed_bytes = 0
    exact_names: set[str] = set()
    folded_names: set[str] = set()
    file_paths: list[str] = []
    try:
        archive = tarfile.open(path, mode="r:gz")
    except tarfile.TarError as error:
        raise ArchiveSecurityError("archive is not a valid tar.gz file") from error
    with archive:
        for member in archive:
            member_count += 1
            if member_count > MAX_MEMBER_COUNT:
                raise ArchiveSecurityError("archive member count exceeds limit")
            normalized = _validate_member_name(member.name)
            normalized_name = normalized.as_posix()
            folded = normalized_name.casefold()
            if normalized_name in exact_names:
                raise ArchiveSecurityError(f"duplicate archive path: {normalized_name}")
            if folded in folded_names:
                raise ArchiveSecurityError(
                    f"case-folded duplicate archive path: {normalized_name}"
                )
            exact_names.add(normalized_name)
            folded_names.add(folded)
            if member.issym() or member.islnk() or member.isdev() or member.isfifo():
                raise ArchiveSecurityError(
                    f"unsupported archive member type: {normalized_name}"
                )
            if not (member.isfile() or member.isdir()):
                raise ArchiveSecurityError(
                    f"unsupported archive member: {normalized_name}"
                )
            if member.size < 0:
                raise ArchiveSecurityError(
                    f"negative archive member size: {normalized_name}"
                )
            if member.size > MAX_SINGLE_MEMBER_BYTES:
                raise ArchiveSecurityError(
                    f"archive member exceeds size limit: {normalized_name}"
                )
            uncompressed_bytes += member.size
            if uncompressed_bytes > MAX_UNCOMPRESSED_BYTES:
                raise ArchiveSecurityError("archive uncompressed size exceeds limit")
            if member.isfile():
                file_paths.append(normalized_name)
    return ArchiveInspection(
        member_count=member_count,
        uncompressed_bytes=uncompressed_bytes,
        file_paths=tuple(sorted(file_paths)),
    )


def extract_archive_safely(
    archive_path: Path,
    destination: Path,
) -> ArchiveInspection:
    inspection = inspect_archive(archive_path)
    if destination.exists():
        raise ArchiveSecurityError(f"staging destination already exists: {destination}")
    destination.mkdir(parents=True, mode=0o700)
    destination_root = destination.resolve()
    try:
        with tarfile.open(archive_path, mode="r:gz") as archive:
            for member in archive:
                relative = _validate_member_name(member.name)
                target = (destination / relative).resolve()
                if (
                    target != destination_root
                    and destination_root not in target.parents
                ):
                    raise ArchiveSecurityError(
                        f"archive member escapes destination: {member.name}"
                    )
                if member.isdir():
                    target.mkdir(
                        parents=True,
                        exist_ok=True,
                        mode=0o755,
                    )
                    continue
                target.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                    mode=0o755,
                )
                source = archive.extractfile(member)
                if source is None:
                    raise ArchiveSecurityError(
                        f"unable to read archive member: {member.name}"
                    )
                descriptor = os.open(
                    target,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o644,
                )
                try:
                    with os.fdopen(descriptor, "wb") as output:
                        shutil.copyfileobj(
                            source,
                            output,
                            length=1024 * 1024,
                        )
                        output.flush()
                        os.fsync(output.fileno())
                finally:
                    source.close()
        return inspection
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
