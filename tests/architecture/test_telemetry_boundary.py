from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TELEMETRY = ROOT / "src/l9_debt_lsp/telemetry"
PROHIBITED_IMPORTS = (
    "git",
    "dulwich",
    "subprocess",
    "sqlite3",
)
PROHIBITED_TERMS = (
    "document_text",
    "source_content",
    "preview_diff",
    "diagnostic_message",
    "workspace_uri",
    "document_uri",
    "developer_email",
    "developer_name",
    "repository_remote",
    "branch_name",
    "commit_sha",
    "corpus_compiler",
    "mine_patterns",
)


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module)
    return modules


def test_telemetry_imports_no_mutation_systems() -> None:
    for path in TELEMETRY.rglob("*.py"):
        for module in imported_modules(path):
            assert not module.startswith(PROHIBITED_IMPORTS), (
                f"{path} imports prohibited module {module}"
            )


def test_prohibited_fields_exist_only_in_privacy_guard() -> None:
    for path in TELEMETRY.rglob("*.py"):
        if path.name == "privacy.py":
            continue
        content = path.read_text(encoding="utf-8").lower()
        for term in PROHIBITED_TERMS:
            assert term not in content, (
                f"{path} references prohibited telemetry field {term}"
            )
