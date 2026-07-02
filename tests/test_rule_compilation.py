"""Tests for corpus_compiler.py — rule compilation from intelligence outputs."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

from rules_loader import BUILTIN_RULES, RulesLoader


def test_builtin_rules_have_required_fields() -> None:
    required_fields = {"id", "language", "topology", "severity", "patterns", "message"}
    for rule in BUILTIN_RULES:
        missing = required_fields - set(rule.keys())
        assert not missing, f"Rule {rule.get('id')} missing fields: {missing}"


def test_builtin_rules_cover_all_known_rule_ids() -> None:
    """All five resolver-canonical rule IDs must be present in builtins."""
    canonical_ids = {"CI-IMPORT-001", "CI-DEPS-001", "CI-DEPS-002", "API-DRIFT-001", "DOCTRINE"}
    builtin_ids = {r["id"] for r in BUILTIN_RULES}
    missing = canonical_ids - builtin_ids
    assert not missing, f"Missing canonical rule IDs in builtins: {missing}"


def test_rules_loader_falls_back_to_builtins_when_file_absent() -> None:
    loader = RulesLoader(Path("/nonexistent/path/compiled_rules.json"))
    assert len(loader.rules) == len(BUILTIN_RULES)
    assert loader.rules is not BUILTIN_RULES  # must be a copy


def test_rules_loader_loads_from_valid_json() -> None:
    custom_rule = {
        "id": "CUSTOM-001",
        "language": ["python"],
        "topology": "api_drift",
        "severity": "warning",
        "patterns": ["my_pattern"],
        "negative_patterns": [],
        "message": "Custom rule message",
        "quick_fix": None,
    }
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump([custom_rule], f)
        tmp_path = Path(f.name)

    try:
        loader = RulesLoader(tmp_path)
        assert len(loader.rules) == 1
        assert loader.rules[0]["id"] == "CUSTOM-001"
    finally:
        tmp_path.unlink()


def test_rules_loader_reload_replaces_rules() -> None:
    loader = RulesLoader(Path("/nonexistent/compiled_rules.json"))
    initial_count = len(loader.rules)

    new_rule = {"id": "NEW-001", "language": ["yaml"], "topology": "gha_workflow",
                "severity": "info", "patterns": ["pattern"], "negative_patterns": [],
                "message": "msg", "quick_fix": None}

    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        json.dump([new_rule], f)
        tmp_path = Path(f.name)

    try:
        loader.reload(tmp_path)
        assert len(loader.rules) == 1
        assert loader.rules[0]["id"] == "NEW-001"
    finally:
        tmp_path.unlink()


def test_doctrine_quick_fix_is_none() -> None:
    """Doctrine violations must never have a quick_fix — auto-patching doctrine is disallowed."""
    doctrine_rules = [r for r in BUILTIN_RULES if r["id"] == "DOCTRINE"]
    assert doctrine_rules, "DOCTRINE rule not found in builtins"
    assert doctrine_rules[0]["quick_fix"] is None, (
        "DOCTRINE rule has a quick_fix — this violates the no-auto-patch invariant."
    )
