"""Detect topology class of a file URI to pre-filter applicable rules.

Topology classes mirror the corpus.schema.json `topology` enum:
  gha_workflow | python_deps | api_drift | test_isolation |
  doctrine_violation | semantic_tolerance | unclassified

Source: cryptoxdog/l9-ci-debt-intelligence/schemas/corpus.schema.json
"""
from __future__ import annotations

from pathlib import Path


def detect_topology(uri: str) -> str:
    """
    Return the topology class string for a given document URI.
    Used by diagnostics.py to skip irrelevant rules before pattern matching.
    """
    path = Path(uri.replace("file://", ""))
    name = path.name.lower()
    parts = [p.lower() for p in path.parts]

    # GHA workflow files
    if ".github" in parts and "workflows" in parts and path.suffix in (".yml", ".yaml"):
        return "gha_workflow"

    # Python dependency manifest
    if name == "pyproject.toml" or name == "setup.cfg" or name == "requirements.txt":
        return "python_deps"

    # Python source
    if path.suffix == ".py":
        # Heuristic: test files → test_isolation; others → api_drift or doctrine_violation
        if "test" in name or "test" in parts:
            return "test_isolation"
        return "api_drift"  # default for .py; diagnostics further narrow by pattern

    return "unclassified"


def filter_rules_by_topology(
    rules: list[dict],
    topology: str,
) -> list[dict]:
    """
    Return rules whose topology matches the detected file topology,
    plus rules with no topology constraint.
    """
    filtered = []
    for rule in rules:
        rule_topology = rule.get("topology")
        if rule_topology is None or rule_topology == topology:
            filtered.append(rule)
        # doctrine_violation rules apply to any Python file
        elif rule_topology == "doctrine_violation" and topology in ("api_drift", "test_isolation"):
            filtered.append(rule)
    return filtered
