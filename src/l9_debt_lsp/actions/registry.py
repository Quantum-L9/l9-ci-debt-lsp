from __future__ import annotations

from pathlib import Path
from typing import Any

from l9_debt_lsp.packs.jsonio import load_json


class RemediationRegistry:
    """Read remediation templates from the active immutable pack."""

    def templates_for_rule(
        self,
        *,
        pack_root: Path,
        canonical_rule_id: str,
    ) -> list[dict[str, Any]]:
        registry_path = pack_root / "remediations/index.json"
        if not registry_path.is_file():
            return []
        index = load_json(registry_path)
        entries = index.get("templates", [])
        if not isinstance(entries, list):
            return []
        templates: list[dict[str, Any]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if entry.get("canonical_rule_id") != canonical_rule_id:
                continue
            relative_path = entry.get("path")
            if not isinstance(relative_path, str):
                continue
            path = pack_root / relative_path
            if not path.is_file():
                continue
            templates.append(load_json(path))
        return templates
