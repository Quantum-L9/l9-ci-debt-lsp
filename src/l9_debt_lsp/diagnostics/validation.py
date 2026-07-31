from __future__ import annotations

from pathlib import Path
from typing import Any

from l9_debt_lsp.contracts.schema import SchemaValidator

from .errors import FindingValidationError


class FindingValidator:
    def __init__(self, schema_path: Path) -> None:
        self._validator = SchemaValidator(schema_path)

    def validate(
        self,
        finding: dict[str, Any],
    ) -> None:
        try:
            self._validator.validate(finding)
        except Exception as error:
            raise FindingValidationError(str(error)) from error
