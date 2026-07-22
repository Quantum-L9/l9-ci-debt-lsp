# --- L9_META ---
# l9_schema: 1
# origin: l9-ci-debt-lsp
# engine: lsp-server
# layer: [corpus, integration]
# tags: [highway, corpus, refresh, rules]
# owner: platform
# status: active
# --- /L9_META ---
"""Corpus Highway Refresh — ingest compiled rules from .l9/corpus/rules/ channel.

This module provides an alternative rule refresh path that reads directly
from the shared corpus directory, bypassing the full intelligence compilation
pipeline. Use when the harness or another producer has already compiled rules.

Usage:
    python3.12 server/corpus_refresh.py --corpus-dir .l9/corpus
    python3.12 server/corpus_refresh.py --corpus-dir /path/to/sibling-repo/.l9/corpus
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refresh_from_corpus(
    corpus_dir: Path,
    rules_out: Path = Path("rules/compiled_rules.json"),
    lock_out: Path = Path("rules/compiled_rules.lock.json"),
) -> dict:
    """Refresh local rules from the corpus highway.

    Args:
        corpus_dir: Path to the .l9/corpus/ directory (local or sibling repo)
        rules_out: Destination path for compiled_rules.json
        lock_out: Destination path for compiled_rules.lock.json

    Returns:
        Dict with refresh metadata.

    Raises:
        FileNotFoundError: If corpus rules channel has no compiled_rules.json
        ValueError: If the rules file is malformed
    """
    source = corpus_dir / "rules" / "compiled_rules.json"

    if not source.exists():
        raise FileNotFoundError(
            f"No compiled_rules.json found in corpus rules channel at {source}. "
            f"Ensure a producer (e.g., @l9/harness) has written rules to the highway."
        )

    # Validate the source is well-formed JSON with a rules array
    payload = json.loads(source.read_text())
    if isinstance(payload, dict):
        if "rules" not in payload:
            raise ValueError(f"Corpus rules at {source} missing 'rules' array")
        rules = payload["rules"]
    elif isinstance(payload, list):
        rules = payload
        payload = {"rules": rules, "schema_version": "1.0", "producer": "corpus-highway"}
    else:
        raise ValueError(f"Corpus rules at {source} must be JSON object or array")

    if not isinstance(rules, list) or len(rules) == 0:
        raise ValueError(f"Corpus rules at {source} has empty or invalid rules array")

    # Copy to destination
    rules_out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, rules_out)

    # Generate lock file
    lock = {
        "schema_version": str(payload.get("schema_version", "1.0")),
        "artifact_name": str(payload.get("artifact_name", "corpus-highway-rules")),
        "producer": str(payload.get("producer", "corpus-highway")),
        "source_run_id": payload.get("source_run_id"),
        "source_sha": payload.get("source_sha"),
        "rules_sha256": _sha256(rules_out),
        "generated_at": payload.get("generated_at", _utc_now()),
        "refreshed_at": _utc_now(),
        "source": f"corpus-highway:{corpus_dir}",
        "rule_count": len(rules),
        "refresh_command": f"python server/corpus_refresh.py --corpus-dir {corpus_dir}",
    }

    lock_out.parent.mkdir(parents=True, exist_ok=True)
    lock_out.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")

    return {
        "status": "ok",
        "source": str(source),
        "rule_count": len(rules),
        "rules_sha256": lock["rules_sha256"],
        "refreshed_at": lock["refreshed_at"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        required=True,
        help="Path to .l9/corpus/ directory (local or sibling repo)",
    )
    parser.add_argument(
        "--rules-out",
        type=Path,
        default=Path("rules/compiled_rules.json"),
        help="Output path for compiled_rules.json",
    )
    parser.add_argument(
        "--lock-out",
        type=Path,
        default=Path("rules/compiled_rules.lock.json"),
        help="Output path for compiled_rules.lock.json",
    )
    args = parser.parse_args(argv)

    try:
        result = refresh_from_corpus(args.corpus_dir, args.rules_out, args.lock_out)
    except (FileNotFoundError, ValueError) as exc:
        print(f"corpus refresh failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
