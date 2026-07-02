# l9-ci-debt-lsp

IDE-time prevention layer for the L9 CI-debt pipeline.

## Pipeline position

```
l9-ci-debt-resolver        → emits CI_DEBT_FINDINGS.jsonl
l9-ci-debt-intelligence    → compiles rules → outputs/defense/astgrep/rules/
l9-ci-debt-lsp             → loads compiled rules → live editor diagnostics
```

## What it catches (before CI ever runs)

| Rule | File type | Signal |
|---|---|---|
| CI-IMPORT-001 | `.github/workflows/*.yml` | GHA job missing `PYTHONPATH` env var |
| CI-DEPS-001 | `pyproject.toml` | Runtime dep absent from `[project.dependencies]` |
| CI-DEPS-002 | `.github/workflows/*.yml` | Final-Decision/aggregate job missing install step |
| API-DRIFT-001 | `*.py` | `ReviewReport` class missing `suggested_tests` field |
| DOCTRINE | `*.py` | `PacketEnvelope` used as active transport type |

## Architecture

```
VS Code extension (TypeScript)
  └─ language client  →  JSON-RPC  →  pygls LSP server (Python)
                                           └─ rules_loader.py    (compiled_rules.json)
                                           └─ topology_detector.py
                                           └─ diagnostics.py
                                           └─ code_actions.py
                                           └─ corpus_compiler.py (optional refresh)
```

## Quick start

```bash
# 1. Install Python server deps
cd server && pip install -e .

# 2. Install VS Code extension deps
npm install
npm run compile

# 3. Open in VS Code — F5 to launch Extension Development Host
```

## Updating rules from l9-ci-debt-intelligence

```bash
python server/corpus_compiler.py \
  --intelligence-outputs ../l9-ci-debt-intelligence/outputs \
  --out rules/compiled_rules.json
```

## Repos

- Resolver: https://github.com/cryptoxdog/l9-ci-debt-resolver
- Intelligence: https://github.com/cryptoxdog/l9-ci-debt-intelligence
- LSP (this repo): https://github.com/cryptoxdog/l9-ci-debt-lsp
