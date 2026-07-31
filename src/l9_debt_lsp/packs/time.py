from __future__ import annotations

import datetime as dt


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def format_utc(value: dt.datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("time value must be timezone-aware")
    return value.astimezone(dt.UTC).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(dt.UTC)
