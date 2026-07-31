from __future__ import annotations

import datetime as dt
import os
from collections.abc import Iterable
from pathlib import Path

from l9_debt_lsp.contracts.canonical import canonical_json
from l9_debt_lsp.packs.jsonio import (
    load_json,
    write_canonical_json,
)
from l9_debt_lsp.packs.time import parse_utc, utc_now

from .errors import TelemetryStorageError
from .models import TelemetryEvent
from .privacy import validate_privacy

MAX_EVENTS = 10_000
MAX_QUEUE_BYTES = 50 * 1024 * 1024
MAX_DEAD_LETTER = 1000


class TelemetrySpool:
    def __init__(
        self,
        *,
        event_root: Path,
        dead_letter_root: Path,
        retention_days: int,
    ) -> None:
        self.event_root = event_root
        self.dead_letter_root = dead_letter_root
        self.retention_days = retention_days

    def append(self, event: TelemetryEvent) -> Path:
        document = event.as_dict()
        validate_privacy(document)
        destination = self.event_root / f"{event.event_id}.json"
        if destination.exists():
            return destination
        try:
            write_canonical_json(
                destination,
                document,
            )
        except Exception as error:
            raise TelemetryStorageError(
                f"unable to persist telemetry event: {error}"
            ) from error
        self.enforce_limits()
        return destination

    def batch(
        self,
        *,
        maximum_events: int = 100,
        maximum_bytes: int = 1024 * 1024,
    ) -> list[tuple[Path, dict[str, object]]]:
        result: list[tuple[Path, dict[str, object]]] = []
        size = 0
        candidates: list[tuple[str, str, Path, dict[str, object]]] = []
        for path in self.event_root.glob("event_*.json"):
            try:
                document = load_json(path)
                validate_privacy(document)
                candidates.append(
                    (
                        str(document["occurred_at"]),
                        str(document["event_id"]),
                        path,
                        document,
                    )
                )
            except Exception:
                self.move_to_dead_letter(
                    path,
                    reason="invalid_local_event",
                )
        candidates.sort(
            key=lambda value: (
                value[0],
                value[1],
            )
        )
        for _, _, path, document in candidates:
            encoded_size = len(canonical_json(document)) + 1
            if result and (
                len(result) >= maximum_events or size + encoded_size > maximum_bytes
            ):
                break
            if encoded_size > maximum_bytes:
                self.move_to_dead_letter(
                    path,
                    reason="event_exceeds_batch_limit",
                )
                continue
            result.append((path, document))
            size += encoded_size
        return result

    def acknowledge(self, paths: Iterable[Path]) -> None:
        for path in paths:
            path.unlink(missing_ok=True)

    def move_to_dead_letter(
        self,
        path: Path,
        *,
        reason: str,
    ) -> None:
        if not path.exists():
            return
        destination = self.dead_letter_root / path.name
        if destination.exists():
            path.unlink(missing_ok=True)
            return
        os.replace(path, destination)
        write_canonical_json(
            destination.with_suffix(".reason.json"),
            {
                "schema_version": ("l9.telemetry-dead-letter/v1"),
                "event_file": destination.name,
                "reason": reason,
            },
        )
        self._enforce_dead_letter_limit()

    def enforce_limits(self) -> None:
        files = sorted(
            self.event_root.glob("event_*.json"),
            key=lambda path: path.stat().st_mtime,
        )
        cutoff = utc_now() - dt.timedelta(days=self.retention_days)
        for path in list(files):
            try:
                document = load_json(path)
                occurred_at = parse_utc(str(document["occurred_at"]))
                if occurred_at < cutoff:
                    path.unlink(missing_ok=True)
            except Exception:
                self.move_to_dead_letter(
                    path,
                    reason="retention_parse_failure",
                )
        files = sorted(
            self.event_root.glob("event_*.json"),
            key=lambda path: path.stat().st_mtime,
        )
        while len(files) > MAX_EVENTS:
            files.pop(0).unlink(missing_ok=True)
        total = sum(path.stat().st_size for path in files)
        while files and total > MAX_QUEUE_BYTES:
            path = files.pop(0)
            total -= path.stat().st_size
            path.unlink(missing_ok=True)

    def clear(self) -> None:
        for root in (
            self.event_root,
            self.dead_letter_root,
        ):
            for path in root.iterdir():
                if path.is_file():
                    path.unlink(missing_ok=True)

    def statistics(self) -> dict[str, int | float | None]:
        files = list(self.event_root.glob("event_*.json"))
        queued_bytes = sum(path.stat().st_size for path in files)
        oldest_age: float | None = None
        if files:
            oldest_mtime = min(path.stat().st_mtime for path in files)
            oldest_age = max(
                0.0,
                utc_now().timestamp() - oldest_mtime,
            )
        dead_letter_count = len(list(self.dead_letter_root.glob("event_*.json")))
        return {
            "queued_event_count": len(files),
            "queued_bytes": queued_bytes,
            "oldest_event_age_seconds": oldest_age,
            "dead_letter_count": dead_letter_count,
        }

    def _enforce_dead_letter_limit(self) -> None:
        files = sorted(
            self.dead_letter_root.glob("event_*.json"),
            key=lambda path: path.stat().st_mtime,
        )
        while len(files) > MAX_DEAD_LETTER:
            path = files.pop(0)
            path.unlink(missing_ok=True)
            path.with_suffix(".reason.json").unlink(missing_ok=True)
