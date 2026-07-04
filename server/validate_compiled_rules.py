"""Validate the compiled rule bundle consumed by l9-ci-debt-lsp."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

_ALLOWED_SEVERITIES = {"error", "warning", "info", "hint"}
_ALLOWED_PATTERN_TYPES = {"regex"}
_ALLOWED_LANGUAGES = {"yaml", "python", "toml", "json", "typescript"}
_REQUIRED_RULE_FIELDS = {
    "id",
    "language",
    "topology",
    "severity",
    "pattern_type",
    "patterns",
    "negative_patterns",
    "message",
    "source",
}


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc


def _rules_payload(data: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if isinstance(data, list):
        return {"schema_version": "legacy-list", "rules": data}, data
    if not isinstance(data, dict):
        raise ValueError("compiled rules must be a JSON object or legacy rule list")
    rules = data.get("rules")
    if not isinstance(rules, list):
        raise ValueError("compiled rules object must contain rules array")
    return data, rules


def _validate_regex_list(rule_id: str, field: str, patterns: Any) -> list[str]:
    if not isinstance(patterns, list):
        raise ValueError(f"{rule_id}: {field} must be an array")
    for idx, pattern in enumerate(patterns):
        if not isinstance(pattern, str):
            raise ValueError(f"{rule_id}: {field}[{idx}] must be a string")
        try:
            re.compile(pattern)
        except re.error as exc:
            raise ValueError(f"{rule_id}: {field}[{idx}] invalid regex: {exc}") from exc
    return patterns


def validate_rules_bundle(rules_path: Path, lock_path: Path | None = None) -> dict[str, Any]:
    payload, rules = _rules_payload(_load_json(rules_path))
    errors: list[str] = []
    seen_ids: set[str] = set()

    if not rules:
        errors.append("rules array must not be empty")

    if payload.get("producer") not in {None, "l9-ci-debt-intelligence"}:
        errors.append("producer must be l9-ci-debt-intelligence")
    if payload.get("artifact_name") not in {None, "ci-debt-intelligence-compiled-rules"}:
        errors.append("artifact_name must be ci-debt-intelligence-compiled-rules")

    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            errors.append(f"rules[{index}] must be an object")
            continue
        missing = sorted(_REQUIRED_RULE_FIELDS - set(rule))
        rule_id = str(rule.get("id", f"rules[{index}]"))
        if missing:
            errors.append(f"{rule_id}: missing required fields: {', '.join(missing)}")
        if not isinstance(rule.get("id"), str) or not rule.get("id"):
            errors.append(f"rules[{index}]: id must be non-empty string")
        elif rule_id in seen_ids:
            errors.append(f"{rule_id}: duplicate rule id")
        else:
            seen_ids.add(rule_id)

        languages = rule.get("language")
        if not isinstance(languages, list) or not languages:
            errors.append(f"{rule_id}: language must be a non-empty array")
        else:
            invalid_languages = [lang for lang in languages if lang not in _ALLOWED_LANGUAGES]
            if invalid_languages:
                errors.append(f"{rule_id}: unsupported languages: {invalid_languages}")

        if rule.get("severity") not in _ALLOWED_SEVERITIES:
            errors.append(f"{rule_id}: severity must be one of {sorted(_ALLOWED_SEVERITIES)}")
        if rule.get("pattern_type") not in _ALLOWED_PATTERN_TYPES:
            errors.append(f"{rule_id}: pattern_type must be regex")
        if not isinstance(rule.get("message"), str) or not rule.get("message"):
            errors.append(f"{rule_id}: message must be non-empty")
        if not isinstance(rule.get("source"), str) or not rule.get("source"):
            errors.append(f"{rule_id}: source must be non-empty")

        try:
            _validate_regex_list(rule_id, "patterns", rule.get("patterns"))
            _validate_regex_list(rule_id, "negative_patterns", rule.get("negative_patterns"))
        except ValueError as exc:
            errors.append(str(exc))

        quick_fix = rule.get("quick_fix")
        if quick_fix is not None:
            if not isinstance(quick_fix, dict):
                errors.append(f"{rule_id}: quick_fix must be object or null")
            else:
                for field in ("label", "insert_after_pattern", "insert_text"):
                    if not isinstance(quick_fix.get(field), str) or not quick_fix.get(field):
                        errors.append(f"{rule_id}: quick_fix.{field} must be non-empty string")
                if isinstance(quick_fix.get("insert_after_pattern"), str):
                    try:
                        re.compile(quick_fix["insert_after_pattern"])
                    except re.error as exc:
                        errors.append(f"{rule_id}: quick_fix.insert_after_pattern invalid regex: {exc}")

    lock_data: dict[str, Any] | None = None
    if lock_path:
        lock_data = _load_json(lock_path)
        if not isinstance(lock_data, dict):
            errors.append("lock file must be a JSON object")
        else:
            if lock_data.get("artifact_name") != "ci-debt-intelligence-compiled-rules":
                errors.append("lock artifact_name must be ci-debt-intelligence-compiled-rules")
            if lock_data.get("producer") != "l9-ci-debt-intelligence":
                errors.append("lock producer must be l9-ci-debt-intelligence")
            locked_hash = lock_data.get("rules_sha256")
            if locked_hash:
                actual_hash = hashlib.sha256(rules_path.read_bytes()).hexdigest()
                if actual_hash != locked_hash:
                    errors.append(
                        f"rules_sha256 mismatch: lock={locked_hash} actual={actual_hash} "
                        "(run refresh_rules.py to regenerate the lock)"
                    )

    if errors:
        raise ValueError("\n".join(f"- {error}" for error in errors))

    return {
        "status": "pass",
        "rules_path": str(rules_path),
        "lock_path": str(lock_path) if lock_path else None,
        "rule_count": len(rules),
        "rule_ids": sorted(seen_ids),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rules", type=Path, default=Path("rules/compiled_rules.json"))
    parser.add_argument("--lock", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        result = validate_rules_bundle(args.rules, args.lock)
    except ValueError as exc:
        print("compiled rules validation failed:", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
