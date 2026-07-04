from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_active_compiled_rules_validate() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "server" / "validate_compiled_rules.py"),
            "--rules",
            str(ROOT / "rules" / "compiled_rules.json"),
            "--lock",
            str(ROOT / "rules" / "compiled_rules.lock.json"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["status"] == "pass"
    assert payload["rule_count"] >= 1
    assert "CI-IMPORT-001" in payload["rule_ids"]


def test_refresh_from_intelligence_fixture(tmp_path: Path) -> None:
    rules_out = tmp_path / "compiled_rules.json"
    lock_out = tmp_path / "compiled_rules.lock.json"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "server" / "refresh_rules.py"),
            "--intelligence-outputs",
            str(ROOT / "fixtures" / "intelligence" / "outputs"),
            "--rules-out",
            str(rules_out),
            "--lock-out",
            str(lock_out),
            "--expected-schema-version",
            "1.0",
            "--expected-artifact-name",
            "ci-debt-intelligence-compiled-rules",
            "--source-run-id",
            "pytest",
            "--source-sha",
            "pytest-sha",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["validation"]["status"] == "pass"
    assert rules_out.exists()
    assert lock_out.exists()
    lock = json.loads(lock_out.read_text())
    assert lock["artifact_name"] == "ci-debt-intelligence-compiled-rules"
    assert lock["rules_sha256"]
