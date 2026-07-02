"""Compile compiled_rules.json from l9-ci-debt-intelligence defense outputs.

This script is the handoff point between the intelligence pipeline and the
LSP server. It reads:
  <intelligence-outputs>/defense/astgrep/rules/*.yaml
  <intelligence-outputs>/offense/generated_invariants.yaml

And writes:
  <out>  (default: rules/compiled_rules.json)

The output format is a JSON array of rule objects matching the RulesLoader
expectation in server/rules_loader.py.

Source repos:
  cryptoxdog/l9-ci-debt-resolver  — classification-rules.md (canonical rule IDs)
  cryptoxdog/l9-ci-debt-intelligence — defense/astgrep/rules/*.yaml (compiled patterns)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import typer
import yaml

app = typer.Typer()

# Severity mapping from intelligence corpus severities → LSP diagnostic severity strings
_SEVERITY_MAP = {
    "critical": "error",
    "high": "error",
    "error": "error",
    "medium": "warning",
    "warning": "warning",
    "low": "info",
    "info": "info",
}

# Language mapping from ast-grep language labels → LSP language IDs
_LANG_MAP = {
    "yaml": "yaml",
    "python": "python",
    "py": "python",
    "toml": "toml",
}

# Topology mapping from rule ID prefixes
_TOPOLOGY_MAP = {
    "CI-IMPORT": "gha_workflow",
    "CI-DEPS": "gha_workflow",
    "API-DRIFT": "api_drift",
    "DOCTRINE": "doctrine_violation",
}


def _rule_id_to_topology(rule_id: str) -> str:
    for prefix, topology in _TOPOLOGY_MAP.items():
        if rule_id.upper().startswith(prefix):
            return topology
    return "unclassified"


def _astgrep_rule_to_lsp(rule_dict: dict) -> dict | None:
    """
    Convert an ast-grep rule YAML dict to the LSP rule format.
    Returns None if the rule cannot be converted (no usable pattern).
    """
    rule_id = rule_dict.get("id", "").upper().replace("-", "-")
    if not rule_id:
        return None

    language_raw = rule_dict.get("language", "yaml")
    language = [_LANG_MAP.get(language_raw.lower(), language_raw.lower())]

    # Extract pattern string from ast-grep rule structure
    rule_body = rule_dict.get("rule", {})
    pattern_str = rule_body.get("pattern") or rule_body.get("regex", "")

    if not pattern_str:
        return None  # No usable pattern — skip

    severity_raw = rule_dict.get("severity", "warning")
    severity = _SEVERITY_MAP.get(severity_raw.lower(), "warning")

    message = rule_dict.get("message", f"{rule_id} violation")
    # Append resolver docs link if not already present
    if "github.com/cryptoxdog" not in message:
        message += (
            f" See: https://github.com/cryptoxdog/l9-ci-debt-resolver/blob/main/"
            f"references/classification-rules.md"
        )

    return {
        "id": rule_id,
        "language": language,
        "topology": _rule_id_to_topology(rule_id),
        "severity": severity,
        "pattern_type": "regex",
        "patterns": [pattern_str],
        "negative_patterns": [],
        "message": message,
        "quick_fix": None,
        "source": "l9-ci-debt-intelligence",
    }


@app.command()
def compile_rules(
    intelligence_outputs: Path = typer.Option(
        ...,
        "--intelligence-outputs",
        help="Path to l9-ci-debt-intelligence/outputs directory",
    ),
    out: Path = typer.Option(
        Path(__file__).parent.parent / "rules" / "compiled_rules.json",
        help="Output path for compiled_rules.json",
    ),
) -> None:
    """
    Compile LSP rules from l9-ci-debt-intelligence astgrep outputs and
    generated invariants. Writes compiled_rules.json consumed by rules_loader.py.
    """
    rules: list[dict] = []
    skipped = 0

    # 1. Load ast-grep rule YAMLs from defense outputs
    astgrep_dir = intelligence_outputs / "defense" / "astgrep" / "rules"
    if astgrep_dir.exists():
        for rule_file in sorted(astgrep_dir.glob("*.yaml")):
            try:
                rule_dict = yaml.safe_load(rule_file.read_text())
                converted = _astgrep_rule_to_lsp(rule_dict)
                if converted:
                    rules.append(converted)
                else:
                    skipped += 1
                    typer.echo(f"  SKIP (no pattern): {rule_file.name}")
            except Exception as exc:
                typer.echo(f"  ERROR loading {rule_file.name}: {exc}", err=True)
                skipped += 1
    else:
        typer.echo(f"WARN: astgrep rules dir not found: {astgrep_dir}")

    # 2. Load generated invariants for additional rule IDs not in astgrep
    invariants_path = intelligence_outputs / "offense" / "generated_invariants.yaml"
    if invariants_path.exists():
        data = yaml.safe_load(invariants_path.read_text()) or {}
        for inv in data.get("invariants", []):
            inv_id = inv.get("id", "")
            # Skip if already covered by astgrep rules
            if any(r["id"] == inv_id for r in rules):
                continue
            rules.append({
                "id": inv_id,
                "language": ["python", "yaml", "toml"],
                "topology": _rule_id_to_topology(inv_id),
                "severity": "warning",
                "pattern_type": "regex",
                "patterns": [],  # No pattern — surfaces as metadata-only rule
                "negative_patterns": [],
                "message": inv.get("description", f"{inv_id} invariant violation"),
                "quick_fix": None,
                "source": "l9-ci-debt-intelligence/invariants",
            })
    else:
        typer.echo(f"WARN: generated_invariants.yaml not found: {invariants_path}")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rules, indent=2))
    typer.echo(
        f"Compiled {len(rules)} rules ({skipped} skipped) → {out}"
    )


if __name__ == "__main__":
    app()
