# l9-ci-debt-lsp — Package Manifest

## Purpose

IDE-time prevention surface for L9 CI debt. Surfaces known CI failure patterns as
real-time LSP diagnostics and one-click quick fixes **before** a commit reaches CI.
Consumes compiled rule bundles produced by `l9-ci-debt-intelligence`.

## Dependency Chain

```
l9-ci-debt-resolver          # sensor: detects & classifies CI failures
  └─► l9-ci-debt-intelligence  # corpus: learns patterns, generates rule bundles
        └─► l9-ci-debt-lsp      # prevention: surfaces rules in editor at write-time
```

## Deliverables

| Artifact | Path | Description |
|---|---|---|
| VS Code extension | `src/extension.ts` | TypeScript wrapper; activates pygls server |
| pygls LSP server | `server/server.py` | Language server entrypoint |
| Rule engine | `server/rules_loader.py` | Loads + caches compiled rule bundles |
| Diagnostics | `server/diagnostics.py` | Maps rule matches → LSP Diagnostic objects |
| Code actions | `server/code_actions.py` | Maps rules → WorkspaceEdit quick fixes |
| Topology detector | `server/topology_detector.py` | Classifies project type (GHA/Python/Node) |
| Corpus compiler | `server/corpus_compiler.py` | Pulls latest rule bundle from intelligence repo |
| Compiled rules | `rules/compiled_rules.json` | Seeded with 4 known root-cause rules |
| Message templates | `rules/message_templates.yaml` | Human-readable diagnostic messages per rule |
| Commands | `src/commands/` | refreshCorpus, applyQuickFix, openFindingDocs |
| Status bar | `src/views/statusBar.ts` | Active rule count + last-updated indicator |
| Fixtures | `fixtures/` | 4 canonical bad-state files for test assertions |
| Tests | `tests/` | pytest (Python) + ts-jest (TypeScript) suites |
| CI | `.github/workflows/ci.yml` | Python gate + TypeScript compile on every PR |
| Publish | `.github/workflows/publish-extension.yml` | VSIX build + marketplace publish on tag |

## Seeded Rules

| Rule ID | Pattern | Fix |
|---|---|---|
| CI-IMPORT-001 | GHA job missing `PYTHONPATH: ${{ github.workspace }}` | Inject env block |
| CI-DEPS-001 | `pydantic` absent from `pyproject.toml` runtime deps | Add `pydantic>=2.0` |
| API-DRIFT-001 | `report.py` missing `SuggestedTest`, `load_json_report()` | Extend module |
| CI-DEPS-002 | Final-Decision GHA job has no install-deps step | Add `pip install` step |

## Sprint Gate Mapping

| Gate | Requirement | Status |
|---|---|---|
| Day 30 | Rule engine + 4 seeded rules + pytest suite passing | ✅ Initial commit |
| Day 60 | Corpus auto-refresh from intelligence repo + VSIX build passing | 🔲 Pending |
| Day 90 | Marketplace publish + false-positive rate < 5% validated | 🔲 Pending |

## Local Development

```bash
# Python server
pip install -e ".[dev]"
pytest tests/ -q

# TypeScript extension
npm install
npm run compile
npm test

# Pre-commit gates (runs Gate A + B locally)
pip install pre-commit
pre-commit install
pre-commit run --all-files
```
