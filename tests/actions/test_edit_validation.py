from __future__ import annotations

import pytest

from l9_debt_lsp.actions.errors import EditValidationError
from l9_debt_lsp.actions.models import Position, TextEdit
from l9_debt_lsp.actions.positions import (
    apply_edits,
    validate_edits,
)


def test_non_overlapping_edits_apply_deterministically() -> None:
    edits = (
        TextEdit(
            start=Position(0, 0),
            end=Position(0, 1),
            replacement="A",
        ),
        TextEdit(
            start=Position(0, 2),
            end=Position(0, 3),
            replacement="C",
        ),
    )
    validated = validate_edits(
        text="abc",
        edits=edits,
    )
    assert (
        apply_edits(
            text="abc",
            edits=validated,
        )
        == "AbC"
    )


def test_overlapping_edits_are_rejected() -> None:
    edits = (
        TextEdit(
            start=Position(0, 0),
            end=Position(0, 2),
            replacement="x",
        ),
        TextEdit(
            start=Position(0, 1),
            end=Position(0, 3),
            replacement="y",
        ),
    )
    with pytest.raises(EditValidationError):
        validate_edits(
            text="abc",
            edits=edits,
        )
