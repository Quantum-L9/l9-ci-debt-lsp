#!/usr/bin/env python3
"""Evaluate the L9 PR Pipeline Gate for L9 CI-debt nodes.

Debt-node policy (Kernel "build the rails first"):
  - The ONLY hard-blocking condition is a NEWLY-INTRODUCED secret leak
    (secret_scan job conclusion == "failure"). This maps to the Kernel
    finding_policy.hard_block_if_touched: secret_leak.
  - Every other gate is ADVISORY on debt nodes: inherited debt, lint, type,
    audit, semgrep, supply-chain, docs are surfaced but never block merge.
  - Missing / skipped optional jobs are advisory, never blocking, because the
    pipeline is surface-detecting and skips gates when the surface is absent.

Reads a single ci_context.json (path via CI_CONTEXT_PATH, default ci_context.json)
and prints a machine-readable verdict. Exit code 1 == gate blocks merge.
"""

from __future__ import annotations

import json
import os
import sys

FAIL_RESULTS = {"failure", "timed_out", "action_required"}

# Jobs that hard-block the gate on this node class. Kept intentionally minimal.
HARD_BLOCK_JOBS = ("secret_scan",)


def _load_context() -> dict:
    path = os.environ.get("CI_CONTEXT_PATH", "ci_context.json")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[WARN] could not read {path}: {exc}", file=sys.stderr)
        return {}


def main() -> int:
    ctx = _load_context()
    results = ctx.get("results", {}) if isinstance(ctx.get("results"), dict) else {}

    blocking: list[str] = []
    advisory: list[str] = []

    for job in HARD_BLOCK_JOBS:
        result = str(results.get(job, "missing")).lower()
        if result in FAIL_RESULTS:
            blocking.append(f"blocking:{job}:{result}")

    # Secret findings counter is an independent signal (diff-scoped scan).
    secret_findings = int(ctx.get("secret_findings", 0) or 0)
    if secret_findings > 0 and not blocking:
        blocking.append(f"blocking:new_secret_findings:{secret_findings}")

    for job, result in results.items():
        result = str(result).lower()
        if job in HARD_BLOCK_JOBS:
            continue
        if result in FAIL_RESULTS or result == "missing":
            advisory.append(f"advisory:{job}:{result}")

    if ctx.get("diff_unknown"):
        advisory.append("advisory:diff_unknown:conservative_core_gates_ran")

    verdict = {
        "result": "FAIL" if blocking else "PASS",
        "merge_meaning": (
            "blocked_by_real_governance" if blocking else "advisory_only"
        ),
        "blocking": blocking,
        "advisory": advisory,
        "secret_findings": secret_findings,
        "pr_class": ctx.get("pr_class", "unknown"),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as fh:
            fh.write(f"gate_result={verdict['result']}\n")
            fh.write(f"merge_meaning={verdict['merge_meaning']}\n")
            fh.write(f"blocking_count={len(blocking)}\n")

    if blocking:
        print("[FAIL] PR Pipeline Gate: merge blocked by real governance risk.")
        return 1
    print("[PASS] PR Pipeline Gate: no blocking risk (advisories may exist).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
