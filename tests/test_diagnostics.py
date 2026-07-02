"""Tests for diagnostics.py — verifies each rule fires on its fixture.

All fixture files are derived from patterns documented in:
  cryptoxdog/l9-ci-debt-resolver/references/classification-rules.md
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

from rules_loader import BUILTIN_RULES
from diagnostics import compute_diagnostics

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
EXPECTED_PATH = FIXTURES_DIR / "expected_diagnostics.json"

expected = json.loads(EXPECTED_PATH.read_text())


def _uri(fixture_name: str) -> str:
    return f"file://{(FIXTURES_DIR / fixture_name).resolve()}"


@pytest.mark.parametrize(
    "fixture_file,expectations",
    [
        (k.split("/")[-1], v)
        for k, v in expected.items()
        if not k.startswith("_")
    ],
)
def test_fixture_diagnostics(fixture_file: str, expectations: list[dict]) -> None:
    fixture_path = FIXTURES_DIR / fixture_file
    assert fixture_path.exists(), f"Fixture not found: {fixture_path}"

    text = fixture_path.read_text()
    uri = _uri(fixture_file)
    diagnostics = compute_diagnostics(text, uri, BUILTIN_RULES)

    for exp in expectations:
        rule_id = exp["rule_id"]
        matching = [d for d in diagnostics if d.code == rule_id]
        assert len(matching) >= exp["expected_count_min"], (
            f"Expected >= {exp['expected_count_min']} diagnostic(s) for {rule_id} "
            f"in {fixture_file}, got {len(matching)}.\n"
            f"All diagnostics: {[(d.code, d.message[:60]) for d in diagnostics]}"
        )
        for diag in matching:
            assert exp["message_contains"].lower() in diag.message.lower(), (
                f"Diagnostic message for {rule_id} does not contain '{exp['message_contains']}':\n"
                f"  {diag.message[:120]}"
            )


def test_no_false_positives_on_clean_file() -> None:
    """A file with all fixes applied should produce zero diagnostics."""
    clean_yaml = """name: clean-workflow
jobs:
  build:
    runs-on: ubuntu-latest
    env:
      PYTHONPATH: ${{ github.workspace }}
    steps:
      - uses: actions/checkout@v4
      - name: Install deps
        run: pip install pyyaml jsonschema pydantic
"""
    diagnostics = compute_diagnostics(
        clean_yaml,
        "file:///workspace/.github/workflows/clean.yml",
        BUILTIN_RULES,
    )
    ci_import_diags = [d for d in diagnostics if d.code == "CI-IMPORT-001"]
    assert len(ci_import_diags) == 0, (
        f"False positive: CI-IMPORT-001 fired on a clean file.\n"
        f"Diagnostics: {[(d.code, d.message[:60]) for d in ci_import_diags]}"
    )


def test_doctrine_fires_on_packet_envelope() -> None:
    python_with_doctrine_violation = """from transport import PacketEnvelope\n\nclass Sender:\n    envelope = PacketEnvelope()\n"""
    diagnostics = compute_diagnostics(
        python_with_doctrine_violation,
        "file:///workspace/transport/sender.py",
        BUILTIN_RULES,
    )
    doctrine_diags = [d for d in diagnostics if d.code == "DOCTRINE"]
    assert len(doctrine_diags) >= 1, "DOCTRINE rule did not fire on PacketEnvelope usage."


def test_api_drift_fires_on_report_without_suggested_tests() -> None:
    python_missing_field = """from dataclasses import dataclass\n\n@dataclass\nclass ReviewReport:\n    summary: str\n    issues: list\n"""
    diagnostics = compute_diagnostics(
        python_missing_field,
        "file:///workspace/tools/review/report.py",
        BUILTIN_RULES,
    )
    drift_diags = [d for d in diagnostics if d.code == "API-DRIFT-001"]
    assert len(drift_diags) >= 1, "API-DRIFT-001 did not fire on ReviewReport missing suggested_tests."
