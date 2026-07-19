from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = ROOT / "src/l9_debt_lsp/analysis"

FORBIDDEN_IMPORT_PREFIXES = (
    "l9_ci_sdk._",
    "l9_ci_sdk.internal",
    "requests",
    "httpx",
    "aiohttp",
    "sqlite3",
)


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_analysis_runtime_uses_no_network_or_private_sdk() -> None:
    for path in ANALYSIS_ROOT.rglob("*.py"):
        for module in imported_modules(path):
            assert not module.startswith(FORBIDDEN_IMPORT_PREFIXES), (
                f"{path} imports prohibited module {module}"
            )


def test_analysis_runtime_does_not_persist_source_content() -> None:
    prohibited = (
        "write_text(text",
        "write_bytes(text",
        "sqlite3",
        "source_content_log",
    )
    for path in ANALYSIS_ROOT.rglob("*.py"):
        content = path.read_text(encoding="utf-8").lower()
        for term in prohibited:
            assert term not in content, (
                f"{path} contains prohibited persistence term {term}"
            )
