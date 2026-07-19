from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAGNOSTICS = ROOT / "src/l9_debt_lsp/diagnostics"


def test_diagnostics_do_not_generate_sdk_finding_ids() -> None:
    prohibited = (
        'namespaced_hash("finding_',
        "uuid.uuid4",
        "uuid4(",
        "reconstruct_finding",
    )
    for path in DIAGNOSTICS.rglob("*.py"):
        content = path.read_text(encoding="utf-8")
        for term in prohibited:
            assert term not in content, (
                f"{path} contains prohibited finding identity generation: {term}"
            )


def test_diagnostics_do_not_access_corpus() -> None:
    prohibited = (
        "corpus-record",
        "corpus_event",
        "mine_patterns",
        "duckdb",
        "pyarrow",
    )
    for path in DIAGNOSTICS.rglob("*.py"):
        content = path.read_text(encoding="utf-8").lower()
        for term in prohibited:
            assert term not in content, (
                f"{path} contains prohibited corpus dependency {term}"
            )
