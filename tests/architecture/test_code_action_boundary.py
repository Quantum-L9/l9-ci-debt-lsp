from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTIONS = ROOT / "src/l9_debt_lsp/actions"
PROHIBITED_IMPORTS = (
    "subprocess",
    "pty",
    "pexpect",
    "git",
    "dulwich",
    "requests",
    "httpx",
    "aiohttp",
)
PROHIBITED_TERMS = (
    "os.system",
    "shell=true",
    "git checkout",
    "git commit",
    "git push",
    "pip install",
    "npm install",
    "createfile",
    "renamefile",
    "deletefile",
)


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                result.add(node.module)
    return result


def test_actions_execute_no_commands_or_network() -> None:
    for path in ACTIONS.rglob("*.py"):
        for module in imported_modules(path):
            assert not module.startswith(PROHIBITED_IMPORTS), (
                f"{path} imports prohibited module {module}"
            )


def test_actions_contain_no_mutating_command_paths() -> None:
    for path in ACTIONS.rglob("*.py"):
        content = path.read_text(encoding="utf-8").lower()
        for term in PROHIBITED_TERMS:
            assert term not in content, f"{path} contains prohibited operation {term}"
