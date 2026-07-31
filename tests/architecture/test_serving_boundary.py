from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "src/l9_debt_lsp"
FORBIDDEN_MODULE_PREFIXES = (
    "l9_ci_core",
    "l9_ci_debt_resolver",
    "pr_repair",
)
FORBIDDEN_TERMS = (
    "corpus_compiler",
    "intelligenceoutputspath",
    "refreshcorpus",
    "outputs/corpus",
    "mine_patterns",
    "generate_authoritative_rules",
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


def test_runtime_does_not_import_forbidden_repositories() -> None:
    for path in SOURCE_ROOT.rglob("*.py"):
        for module in imported_modules(path):
            assert not module.startswith(FORBIDDEN_MODULE_PREFIXES), (
                f"{path} imports prohibited module {module}"
            )


def test_removed_legacy_terms_do_not_exist_in_runtime() -> None:
    for path in SOURCE_ROOT.rglob("*.py"):
        content = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_TERMS:
            assert term not in content, f"{path} contains prohibited legacy term {term}"


def test_no_legacy_corpus_compiler_exists() -> None:
    assert not (ROOT / "server/corpus_compiler.py").exists()
    assert not (ROOT / "rules/compiled_rules.json").exists()
