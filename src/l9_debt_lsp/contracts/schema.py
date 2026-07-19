from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .errors import SchemaValidationError


class SchemaValidator:
    """Validate JSON documents against a Draft 2020-12 schema."""

    def __init__(self, schema_path: Path) -> None:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self._validator = Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        )

    def validate(self, document: dict[str, Any]) -> None:
        errors = sorted(
            self._validator.iter_errors(document),
            key=lambda error: list(error.absolute_path),
        )
        if not errors:
            return
        messages = []
        for error in errors:
            location = "/".join(str(item) for item in error.absolute_path)
            messages.append(f"{location or '<root>'}: {error.message}")
        raise SchemaValidationError("; ".join(messages))
