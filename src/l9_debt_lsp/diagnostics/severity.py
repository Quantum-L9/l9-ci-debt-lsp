from __future__ import annotations

SEVERITY_MAP = {
    "critical": 1,
    "error": 1,
    "warning": 2,
    "information": 3,
    "info": 3,
    "hint": 4,
    "unknown": 2,
}
SEVERITY_RANK = {
    1: 0,
    2: 1,
    3: 2,
    4: 3,
}
TAG_MAP = {
    "unnecessary": 1,
    "deprecated": 2,
}


def diagnostic_severity(value: str) -> int:
    return SEVERITY_MAP.get(value, 2)


def diagnostic_tags(values: object) -> tuple[int, ...]:
    if not isinstance(values, list):
        return ()
    tags = {
        TAG_MAP[value]
        for value in values
        if isinstance(value, str) and value in TAG_MAP
    }
    return tuple(sorted(tags))
