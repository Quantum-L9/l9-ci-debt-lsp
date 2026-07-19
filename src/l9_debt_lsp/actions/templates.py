from __future__ import annotations

from pathlib import Path
from typing import Any

from l9_debt_lsp.contracts.schema import SchemaValidator

from .errors import TemplateValidationError
from .models import (
    Position,
    RemediationTemplate,
    TextEdit,
)


class TemplateParser:
    def __init__(self, schema_root: Path) -> None:
        self._validator = SchemaValidator(
            schema_root / "quick-fix-template.schema.json"
        )

    def parse(
        self,
        value: dict[str, Any],
    ) -> RemediationTemplate:
        try:
            self._validator.validate(value)
        except Exception as error:
            raise TemplateValidationError(str(error)) from error
        if value["scope"] != "current_document":
            raise TemplateValidationError("only current-document fixes are supported")
        if value["kind"] not in {
            "deterministic_template",
            "validated_structural_rewrite",
        }:
            raise TemplateValidationError("unsupported remediation kind")
        edits = tuple(
            TextEdit(
                start=Position(
                    line=edit["start_line"],
                    character=edit["start_character"],
                ),
                end=Position(
                    line=edit["end_line"],
                    character=edit["end_character"],
                ),
                replacement=edit["replacement"],
            )
            for edit in value["edits"]
        )
        return RemediationTemplate(
            template_id=value["template_id"],
            canonical_rule_id=value["canonical_rule_id"],
            title=value["title"],
            kind=value["kind"],
            safety=value["safety"],
            scope=value["scope"],
            edits=edits,
            limitations=tuple(sorted(set(value["limitations"]))),
        )
