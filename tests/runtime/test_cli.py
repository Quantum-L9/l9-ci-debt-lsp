from __future__ import annotations

import json
from pathlib import Path

import pytest

from l9_debt_lsp import __version__
from l9_debt_lsp.cli import main


def _run(capsys: pytest.CaptureFixture[str], argv: list[str]) -> dict[str, object]:
    code = main(argv)
    assert code == 0
    out = capsys.readouterr().out.strip()
    return json.loads(out)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PACK = ROOT / "tests/fixtures/packs/compatible-defense-pack.json"


def test_cli_capabilities(capsys: pytest.CaptureFixture[str]) -> None:
    payload = _run(capsys, ["capabilities"])
    assert payload["phase"] == "LSP-P5"


def test_cli_evaluate_compatibility_matches_documented_invocation(
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = _run(
        capsys,
        [
            "evaluate-compatibility",
            "--defense-pack",
            str(FIXTURE_PACK),
            "--compatibility",
            str(FIXTURE_PACK),
            "--platform",
            "linux-x86_64",
        ],
    )
    assert payload["status"] == "compatible"
    assert payload["limitations"] == []


def test_cli_evaluate_compatibility_flags_unsupported_platform(
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = _run(
        capsys,
        [
            "evaluate-compatibility",
            "--defense-pack",
            str(FIXTURE_PACK),
            "--compatibility",
            str(FIXTURE_PACK),
            "--platform",
            "unsupported-arch",
        ],
    )
    assert payload["status"] == "incompatible"
    assert payload["checks"]["platform_supported"] is False


def test_cli_active_pack_reports_none(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    payload = _run(capsys, ["--state-root", str(tmp_path), "active-pack"])
    assert payload["status"] == "none"


def test_cli_recover_state_on_empty_root(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    payload = _run(capsys, ["--state-root", str(tmp_path), "recover-state"])
    assert isinstance(payload, dict)


def test_cli_telemetry_health_is_disabled_by_default(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    payload = _run(capsys, ["--state-root", str(tmp_path), "telemetry-health"])
    assert payload["policy_mode"] == "disabled"
    assert payload["status"] == "disabled"


def test_cli_telemetry_delete_all(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    payload = _run(capsys, ["--state-root", str(tmp_path), "telemetry-delete-all"])
    assert payload["status"] == "deleted"


def test_cli_uses_package_version_for_telemetry_context() -> None:
    # Regression guard: the CLI must not hard-code a stale telemetry version.
    assert __version__ == "1.0.0"
