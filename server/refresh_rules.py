"""Refresh the local LSP compiled rules from l9-ci-debt-intelligence outputs."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from corpus_compiler import compile_rules
from validate_compiled_rules import validate_rules_bundle


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_lock(lock_path: Path, result: dict[str, object], expected_artifact_name: str) -> None:
    lock = {
        "schema_version": str(result.get("schema_version") or "1.0"),
        "artifact_name": str(result.get("artifact_name") or expected_artifact_name),
        "producer": str(result.get("producer") or "l9-ci-debt-intelligence"),
        "source_run_id": result.get("source_run_id"),
        "source_sha": result.get("source_sha"),
        "rules_sha256": result.get("rules_sha256"),
        "generated_at": result.get("generated_at"),
        "refreshed_at": _utc_now(),
        "source": result.get("source"),
        "rule_count": result.get("rule_count"),
        "refresh_command": "python server/refresh_rules.py --intelligence-outputs <path-to-intelligence-outputs> --rules-out rules/compiled_rules.json --lock-out rules/compiled_rules.lock.json",
    }
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")


def refresh_rules(
    intelligence_outputs: Path,
    rules_out: Path,
    lock_out: Path,
    expected_schema_version: str,
    expected_artifact_name: str,
    source_run_id: str | None,
    source_sha: str | None,
) -> dict[str, object]:
    result = compile_rules(intelligence_outputs, rules_out, source_run_id=source_run_id, source_sha=source_sha)
    if result.get("schema_version") != expected_schema_version:
        raise ValueError(f"unexpected schema_version: {result.get('schema_version')} != {expected_schema_version}")
    if result.get("artifact_name") != expected_artifact_name:
        raise ValueError(f"unexpected artifact_name: {result.get('artifact_name')} != {expected_artifact_name}")
    _write_lock(lock_out, result, expected_artifact_name)
    validation = validate_rules_bundle(rules_out, lock_out)
    return {"refresh": result, "validation": validation}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intelligence-outputs", type=Path, required=True)
    parser.add_argument("--rules-out", type=Path, default=Path("rules/compiled_rules.json"))
    parser.add_argument("--lock-out", type=Path, default=Path("rules/compiled_rules.lock.json"))
    parser.add_argument("--expected-schema-version", default="1.0")
    parser.add_argument("--expected-artifact-name", default="ci-debt-intelligence-compiled-rules")
    parser.add_argument("--source-run-id", default=None)
    parser.add_argument("--source-sha", default=None)
    args = parser.parse_args(argv)

    try:
        result = refresh_rules(
            args.intelligence_outputs,
            args.rules_out,
            args.lock_out,
            args.expected_schema_version,
            args.expected_artifact_name,
            args.source_run_id,
            args.source_sha,
        )
    except Exception as exc:
        print(f"refresh rules failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
