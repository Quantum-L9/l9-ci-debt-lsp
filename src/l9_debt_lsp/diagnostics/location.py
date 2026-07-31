from __future__ import annotations

from typing import Any

from .errors import SourceLocationError
from .models import Position, Range, SourceLocation


def source_location_from_dict(
    value: dict[str, Any],
) -> SourceLocation:
    try:
        start = Position(
            line=int(value["start_line"]),
            character=int(value["start_character"]),
        )
        end = Position(
            line=int(value["end_line"]),
            character=int(value["end_character"]),
        )
        document_identity = str(value["document_identity"])
        uri = str(value["uri"])
    except (KeyError, TypeError, ValueError) as error:
        raise SourceLocationError("source location is malformed") from error
    if start.line < 0 or start.character < 0 or end.line < 0 or end.character < 0:
        raise SourceLocationError("source location positions must be non-negative")
    if end < start:
        raise SourceLocationError("source location end precedes start")
    if not document_identity:
        raise SourceLocationError("source location document identity is empty")
    if not uri:
        raise SourceLocationError("source location URI is empty")
    return SourceLocation(
        document_identity=document_identity,
        uri=uri,
        range=Range(start=start, end=end),
    )


def clamp_primary_range(
    location: SourceLocation,
    *,
    document_text: str,
) -> Range:
    lines = document_text.splitlines()
    if not lines:
        return Range(
            start=Position(0, 0),
            end=Position(0, 0),
        )
    maximum_line = len(lines) - 1
    start_line = min(location.range.start.line, maximum_line)
    end_line = min(location.range.end.line, maximum_line)
    start_character = min(
        location.range.start.character,
        len(lines[start_line]),
    )
    end_character = min(
        location.range.end.character,
        len(lines[end_line]),
    )
    start = Position(start_line, start_character)
    end = Position(end_line, end_character)
    if end < start:
        end = start
    return Range(start=start, end=end)
