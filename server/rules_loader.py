"""Load compiled_rules.json from l9-ci-debt-intelligence for the LSP server."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# Canonical rule IDs sourced from:
# cryptoxdog/l9-ci-debt-resolver/references/classification-rules.md
# cryptoxdog/l9-ci-debt-intelligence/tools/defense/corpus_to_astgrep.py
BUILTIN_RULES: list[dict[str, Any]] = [
    {
        "id": "CI-IMPORT-001",
        "language": ["yaml"],
        "topology": "gha_workflow",
        "severity": "error",
        "pattern_type": "regex",
        "patterns": [r"^\s{2}[\w-]+:\s*$"],
        "negative_patterns": [r"PYTHONPATH"],
        "message": (
            "CI-IMPORT-001: GHA job missing PYTHONPATH env var. "
            "Add `env: PYTHONPATH: ${{ github.workspace }}` to this job. "
            "See: https://github.com/cryptoxdog/l9-ci-debt-resolver/blob/main/"
            "references/classification-rules.md#p-001-pythonpath-missing-in-ci-job"
        ),
        "quick_fix": {
            "label": "Add PYTHONPATH env var to this job",
            "insert_after_pattern": r"(runs-on:.*)",
            "insert_text": "    env:\n      PYTHONPATH: ${{ github.workspace }}\n",
        },
        "source": "l9-ci-debt-lsp/builtin-fallback",
    },
    {
        "id": "CI-DEPS-001",
        "language": ["toml"],
        "topology": "python_deps",
        "severity": "warning",
        "pattern_type": "regex",
        "patterns": [r"\[project\]"],
        "negative_patterns": [r"\[project\.dependencies\]"],
        "message": (
            "CI-DEPS-001: pyproject.toml missing [project.dependencies] section. "
            "Runtime deps must be declared here — pydantic>=2.0 is a known missing dep. "
            "See: https://github.com/cryptoxdog/l9-ci-debt-resolver/blob/main/"
            "references/classification-rules.md#p-002-runtime-dependency-missing-from-pyprojecttoml"
        ),
        "quick_fix": {
            "label": "Add [project.dependencies] section",
            "insert_after_pattern": r"(\[project\])",
            "insert_text": '\ndependencies = [\n    "pydantic>=2.0",\n]\n',
        },
        "source": "l9-ci-debt-lsp/builtin-fallback",
    },
    {
        "id": "CI-DEPS-002",
        "language": ["yaml"],
        "topology": "gha_workflow",
        "severity": "error",
        "pattern_type": "regex",
        "patterns": [r"(?i)(final.decision|aggregate)[\s\S]*?steps:"],
        "negative_patterns": [r"pip install|uv sync|npm ci"],
        "message": (
            "CI-DEPS-002: Final Decision / aggregate GHA job missing an install-deps step. "
            "Add `pip install` or `uv sync` step before any Python execution. "
            "See: https://github.com/cryptoxdog/l9-ci-debt-resolver/blob/main/"
            "references/classification-rules.md#p-003-ci-job-missing-install-step"
        ),
        "quick_fix": {
            "label": "Add Install deps step to this job",
            "insert_after_pattern": r"(- uses: actions/checkout.*)",
            "insert_text": (
                "      - name: Install deps\n"
                "        run: pip install pyyaml jsonschema pydantic\n"
            ),
        },
        "source": "l9-ci-debt-lsp/builtin-fallback",
    },
    {
        "id": "API-DRIFT-001",
        "language": ["python"],
        "topology": "api_drift",
        "severity": "error",
        "pattern_type": "regex",
        "patterns": [r"class\s+ReviewReport"],
        "negative_patterns": [r"suggested_tests"],
        "message": (
            "API-DRIFT-001: ReviewReport class missing `suggested_tests` field. "
            "Add SuggestedTest dataclass and suggested_tests: list[SuggestedTest] field. "
            "See: https://github.com/cryptoxdog/l9-ci-debt-resolver/blob/main/"
            "references/classification-rules.md#p-004-source-file-missing-exported-symbol"
        ),
        "quick_fix": None,
        "source": "l9-ci-debt-lsp/builtin-fallback",
    },
    {
        "id": "DOCTRINE",
        "language": ["python"],
        "topology": "doctrine_violation",
        "severity": "error",
        "pattern_type": "regex",
        "patterns": [r"PacketEnvelope"],
        "negative_patterns": [],
        "message": (
            "DOCTRINE: PacketEnvelope is not the active transport type. "
            "Use TransportPacket for all wire transport. "
            "Resolution paths: (a) rewrite to TransportPacket-native, "
            "(b) ship a compat adapter in a separate PR with an ADR amendment. "
            "See: https://github.com/cryptoxdog/l9-ci-debt-resolver/blob/main/"
            "references/classification-rules.md#doctrine-violation-response"
        ),
        "quick_fix": None,
        "source": "l9-ci-debt-lsp/builtin-fallback",
    },
]


class RulesLoader:
    """Load compiled rules; fall back to a minimal built-in safety rule if absent."""

    def __init__(self, rules_path: Path) -> None:
        self.rules_path = rules_path
        self.metadata: dict[str, Any] = {}
        self.rules: list[dict[str, Any]] = []
        self.reload(rules_path)

    def reload(self, rules_path: Path) -> None:
        self.rules_path = rules_path
        if not rules_path.exists():
            log.warning("compiled rules not found at %s; using %d built-in fallback rule(s)", rules_path, len(BUILTIN_RULES))
            self.metadata = {"source": "builtin-fallback", "rules_path": str(rules_path)}
            self.rules = list(BUILTIN_RULES)
            return

        try:
            loaded = json.loads(rules_path.read_text())
            if isinstance(loaded, list):
                self.metadata = {"schema_version": "legacy-list", "producer": "Unknown", "artifact_name": "Unknown"}
                self.rules = loaded
            elif isinstance(loaded, dict):
                rules = loaded.get("rules", [])
                if not isinstance(rules, list):
                    raise ValueError("compiled rules object must contain rules array")
                self.metadata = {key: value for key, value in loaded.items() if key != "rules"}
                self.rules = rules
            else:
                raise ValueError("compiled rules JSON must be object or array")
            log.info("Loaded %d compiled rules from %s", len(self.rules), rules_path)
        except Exception as exc:
            log.warning("failed to load %s: %s; using %d built-in fallback rule(s)", rules_path, exc, len(BUILTIN_RULES))
            self.metadata = {"source": "builtin-fallback", "rules_path": str(rules_path), "load_error": str(exc)}
            self.rules = list(BUILTIN_RULES)
