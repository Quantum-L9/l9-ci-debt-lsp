from __future__ import annotations

from .errors import EditValidationError
from .models import Position, TextEdit

MAX_EDITS = 50
MAX_REPLACEMENT_BYTES = 65536
MAX_TOTAL_REPLACEMENT_BYTES = 262144


def line_start_offsets(text: str) -> list[int]:
    offsets = [0]
    for index, character in enumerate(text):
        if character == "\n":
            offsets.append(index + 1)
    return offsets


def character_offset(
    text: str,
    position: Position,
) -> int:
    if position.line < 0 or position.character < 0:
        raise EditValidationError("edit position must be non-negative")
    offsets = line_start_offsets(text)
    if position.line >= len(offsets):
        raise EditValidationError("edit line is outside the document")
    start = offsets[position.line]
    if position.line + 1 < len(offsets):
        line_end = offsets[position.line + 1] - 1
    else:
        line_end = len(text)
    line_text = text[start:line_end]
    if position.character > len(line_text):
        raise EditValidationError("edit character is outside the line")
    return start + position.character


def validate_edits(
    *,
    text: str,
    edits: tuple[TextEdit, ...],
) -> tuple[TextEdit, ...]:
    if not edits:
        raise EditValidationError("a code action requires at least one edit")
    if len(edits) > MAX_EDITS:
        raise EditValidationError(f"edit count exceeds {MAX_EDITS}")
    total_replacement_bytes = 0
    positioned: list[tuple[int, int, TextEdit]] = []
    for edit in edits:
        replacement_bytes = len(edit.replacement.encode("utf-8"))
        if replacement_bytes > MAX_REPLACEMENT_BYTES:
            raise EditValidationError("individual replacement exceeds byte limit")
        total_replacement_bytes += replacement_bytes
        start = character_offset(text, edit.start)
        end = character_offset(text, edit.end)
        if end < start:
            raise EditValidationError("edit end precedes edit start")
        positioned.append((start, end, edit))
    if total_replacement_bytes > MAX_TOTAL_REPLACEMENT_BYTES:
        raise EditValidationError("total replacement bytes exceed limit")
    positioned.sort(
        key=lambda value: (
            value[0],
            value[1],
            value[2].replacement,
        )
    )
    previous_end = -1
    for start, end, _edit in positioned:
        if start < previous_end:
            raise EditValidationError("overlapping edits are prohibited")
        previous_end = max(previous_end, end)
    return tuple(value[2] for value in positioned)


def apply_edits(
    *,
    text: str,
    edits: tuple[TextEdit, ...],
) -> str:
    positioned = [
        (
            character_offset(text, edit.start),
            character_offset(text, edit.end),
            edit.replacement,
        )
        for edit in edits
    ]
    result = text
    for start, end, replacement in sorted(
        positioned,
        key=lambda value: (value[0], value[1]),
        reverse=True,
    ):
        result = result[:start] + replacement + result[end:]
    return result
