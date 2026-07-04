from __future__ import annotations

import json
from pathlib import Path

from server.diagnostics import compute_diagnostics

ROOT = Path(__file__).resolve().parents[1]


def _rules() -> list[dict]:
    return json.loads((ROOT / "rules" / "compiled_rules.json").read_text())["rules"]


def test_bad_workflow_reports_pythonpath_diagnostic() -> None:
    text = (ROOT / "fixtures" / "bad-workflow.yml").read_text()
    diagnostics = compute_diagnostics(text, "file:///tmp/bad-workflow.yml", _rules())
    codes = {str(diagnostic.code) for diagnostic in diagnostics}
    assert "CI-IMPORT-001" in codes


def test_good_workflow_suppresses_pythonpath_diagnostic() -> None:
    text = (ROOT / "fixtures" / "good-workflow.yml").read_text()
    diagnostics = compute_diagnostics(text, "file:///tmp/good-workflow.yml", _rules())
    codes = {str(diagnostic.code) for diagnostic in diagnostics}
    assert "CI-IMPORT-001" not in codes


def test_python_api_drift_reports_diagnostic() -> None:
    text = (ROOT / "fixtures" / "api-drift.py").read_text()
    diagnostics = compute_diagnostics(text, "file:///tmp/api-drift.py", _rules())
    codes = {str(diagnostic.code) for diagnostic in diagnostics}
    assert "API-DRIFT-001" in codes


def test_doctrine_violation_reports_diagnostic() -> None:
    text = (ROOT / "fixtures" / "doctrine-violation.py").read_text()
    diagnostics = compute_diagnostics(text, "file:///tmp/doctrine-violation.py", _rules())
    codes = {str(diagnostic.code) for diagnostic in diagnostics}
    assert "DOCTRINE" in codes
