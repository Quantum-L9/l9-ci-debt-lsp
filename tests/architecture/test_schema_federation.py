from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "schemas"


def test_no_sdk_schema_copies_are_present() -> None:
    prohibited_names = {
        "finding.schema.json",
        "evidence.schema.json",
        "source-location.schema.json",
        "corpus-record.schema.json",
        "corpus-event.schema.json",
    }
    present = {path.name for path in SCHEMA_ROOT.rglob("*.json")}
    assert present.isdisjoint(prohibited_names)


def test_lsp_only_owns_lsp_schemas() -> None:
    for path in SCHEMA_ROOT.rglob("*.json"):
        assert "schemas/lsp/" in path.as_posix()
