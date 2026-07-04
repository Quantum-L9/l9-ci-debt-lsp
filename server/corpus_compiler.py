"""Compile LSP rules from l9-ci-debt-intelligence outputs.

The compiler accepts the PR2 Intelligence artifact contract first:

    <outputs>/compiled-rules/compiled_rules.json

It also accepts compatibility locations used during transition and can derive a
basic compiled bundle from ast-grep YAML files plus generated invariants. The
result is always the LSP compiled-rules object consumed by RulesLoader.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - dependency gate surfaces in fallback path
    yaml = None  # type: ignore[assignment]

_SEVERITY_MAP = {
    "critical": "error",
    "high": "error",
    "error": "error",
    "medium": "warning",
    "warning": "warning",
    "low": "info",
    "info": "info",
    "hint": "hint",
}

_LANG_MAP = {
    "yaml": "yaml",
    "yml": "yaml",
    "python": "python",
    "py": "python",
    "toml": "toml",
    "json": "json",
    "typescript": "typescript",
    "ts": "typescript",
}

_TOPOLOGY_MAP = {
    "CI-IMPORT": "gha_workflow",
    "CI-DEPS": "gha_workflow",
    "API-DRIFT": "api_drift",
    "DOCTRINE": "doctrine_violation",
}

_CANDIDATE_COMPILED_RULES = [
    Path("compiled-rules/compiled_rules.json"),
    Path("defense/compiled_rules.json"),
    Path("defense/lsp/compiled_rules.json"),
    Path("rules/compiled_rules.json"),
]


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _normalise_rule_id(value: Any) -> str:
    return str(value or "").strip().upper()


def _rule_id_to_topology(rule_id: str) -> str:
    for prefix, topology in _TOPOLOGY_MAP.items():
        if rule_id.startswith(prefix):
            return topology
    return "unclassified"


def _as_rules_object(data: Any, source_path: Path, source_run_id: str | None, source_sha: str | None) -> dict[str, Any]:
    if isinstance(data, list):
        rules = data
        producer = "l9-ci-debt-intelligence"
        artifact_name = "ci-debt-intelligence-compiled-rules"
        schema_version = "1.0"
        generated_at = _utc_now()
    elif isinstance(data, dict):
        rules = data.get("rules", [])
        producer = data.get("producer", "l9-ci-debt-intelligence")
        artifact_name = data.get("artifact_name", "ci-debt-intelligence-compiled-rules")
        schema_version = data.get("schema_version", "1.0")
        generated_at = data.get("generated_at", _utc_now())
        source_run_id = source_run_id or data.get("source_run_id")
        source_sha = source_sha or data.get("source_sha")
    else:
        raise ValueError(f"{source_path}: compiled rules must be object or array")

    if not isinstance(rules, list):
        raise ValueError(f"{source_path}: rules must be an array")

    return {
        "schema_version": schema_version,
        "producer": producer,
        "artifact_name": artifact_name,
        "source_run_id": source_run_id,
        "source_sha": source_sha,
        "generated_at": generated_at,
        "rules": rules,
    }


def _find_precompiled(intelligence_outputs: Path) -> Path | None:
    for relative_path in _CANDIDATE_COMPILED_RULES:
        candidate = intelligence_outputs / relative_path
        if candidate.exists():
            return candidate
    return None


def _load_precompiled(path: Path, source_run_id: str | None, source_sha: str | None) -> dict[str, Any]:
    return _as_rules_object(json.loads(path.read_text()), path, source_run_id, source_sha)


def _load_yaml(path: Path) -> Any:
    if yaml is None:
        raise RuntimeError("pyyaml is required when deriving rules from YAML outputs")
    return yaml.safe_load(path.read_text())


def _extract_pattern(rule_dict: dict[str, Any]) -> str:
    body = rule_dict.get("rule", {})
    if isinstance(body, dict):
        pattern = body.get("pattern") or body.get("regex")
        if pattern:
            return str(pattern)
    pattern = rule_dict.get("pattern") or rule_dict.get("regex")
    return str(pattern or "")


def _astgrep_rule_to_lsp(rule_dict: dict[str, Any]) -> dict[str, Any] | None:
    rule_id = _normalise_rule_id(rule_dict.get("id"))
    if not rule_id:
        return None
    pattern = _extract_pattern(rule_dict)
    if not pattern:
        return None

    language_raw = str(rule_dict.get("language", "yaml")).lower()
    language = _LANG_MAP.get(language_raw, language_raw)
    severity_raw = str(rule_dict.get("severity", "warning")).lower()
    severity = _SEVERITY_MAP.get(severity_raw, "warning")

    return {
        "id": rule_id,
        "language": [language],
        "topology": _rule_id_to_topology(rule_id),
        "severity": severity,
        "pattern_type": "regex",
        "patterns": [pattern],
        "negative_patterns": [str(p) for p in rule_dict.get("negative_patterns", [])],
        "message": str(rule_dict.get("message") or f"{rule_id} violation"),
        "quick_fix": rule_dict.get("quick_fix"),
        "source": "l9-ci-debt-intelligence/defense/astgrep/rules",
    }


def _invariant_to_lsp(invariant: dict[str, Any], covered_rule_ids: set[str]) -> dict[str, Any] | None:
    rule_id = _normalise_rule_id(invariant.get("id"))
    if not rule_id or rule_id in covered_rule_ids:
        return None
    pattern = invariant.get("regex") or invariant.get("pattern")
    if not pattern:
        return None
    return {
        "id": rule_id,
        "language": ["python", "yaml", "toml"],
        "topology": _rule_id_to_topology(rule_id),
        "severity": _SEVERITY_MAP.get(str(invariant.get("severity", "warning")).lower(), "warning"),
        "pattern_type": "regex",
        "patterns": [str(pattern)],
        "negative_patterns": [str(p) for p in invariant.get("negative_patterns", [])],
        "message": str(invariant.get("description") or invariant.get("message") or f"{rule_id} invariant violation"),
        "quick_fix": None,
        "source": "l9-ci-debt-intelligence/offense/generated_invariants.yaml",
    }


def _derive_from_outputs(intelligence_outputs: Path, source_run_id: str | None, source_sha: str | None) -> dict[str, Any]:
    rules: list[dict[str, Any]] = []
    astgrep_dir = intelligence_outputs / "defense" / "astgrep" / "rules"
    if astgrep_dir.exists():
        for rule_file in sorted(astgrep_dir.glob("*.y*ml")):
            data = _load_yaml(rule_file) or {}
            if not isinstance(data, dict):
                continue
            converted = _astgrep_rule_to_lsp(data)
            if converted:
                rules.append(converted)

    covered = {rule["id"] for rule in rules}
    invariants_path = intelligence_outputs / "offense" / "generated_invariants.yaml"
    if invariants_path.exists():
        data = _load_yaml(invariants_path) or {}
        if isinstance(data, dict):
            for invariant in data.get("invariants", []):
                if isinstance(invariant, dict):
                    converted = _invariant_to_lsp(invariant, covered)
                    if converted:
                        rules.append(converted)
                        covered.add(converted["id"])

    return {
        "schema_version": "1.0",
        "producer": "l9-ci-debt-intelligence",
        "artifact_name": "ci-debt-intelligence-compiled-rules",
        "source_run_id": source_run_id,
        "source_sha": source_sha,
        "generated_at": _utc_now(),
        "rules": rules,
    }


def _compile_bundle(intelligence_outputs: Path, source_run_id: str | None, source_sha: str | None) -> tuple[dict[str, Any], str]:
    precompiled = _find_precompiled(intelligence_outputs)
    if precompiled:
        return _load_precompiled(precompiled, source_run_id, source_sha), str(precompiled)
    return _derive_from_outputs(intelligence_outputs, source_run_id, source_sha), str(intelligence_outputs)


def compile_rules(intelligence_outputs: Path, out: Path, source_run_id: str | None = None, source_sha: str | None = None) -> dict[str, Any]:
    bundle, source_label = _compile_bundle(intelligence_outputs, source_run_id, source_sha)
    rules = bundle.get("rules", [])
    if not rules:
        raise ValueError(f"no compiled rules found in {intelligence_outputs}")
    for rule in rules:
        for pattern in rule.get("patterns", []):
            re.compile(pattern)
        for pattern in rule.get("negative_patterns", []):
            re.compile(pattern)
        quick_fix = rule.get("quick_fix")
        if isinstance(quick_fix, dict) and quick_fix.get("insert_after_pattern"):
            re.compile(str(quick_fix["insert_after_pattern"]))

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n")
    return {
        "rules_path": str(out),
        "rules_sha256": _sha256_file(out),
        "rule_count": len(rules),
        "source": source_label,
        "schema_version": bundle.get("schema_version"),
        "artifact_name": bundle.get("artifact_name"),
        "producer": bundle.get("producer"),
        "source_run_id": bundle.get("source_run_id"),
        "source_sha": bundle.get("source_sha"),
        "generated_at": bundle.get("generated_at"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intelligence-outputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("rules/compiled_rules.json"))
    parser.add_argument("--source-run-id", default=None)
    parser.add_argument("--source-sha", default=None)
    args = parser.parse_args(argv)

    try:
        result = compile_rules(args.intelligence_outputs, args.out, args.source_run_id, args.source_sha)
    except Exception as exc:
        print(f"compile rules failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
