# PR3 LSP Commit Pack Manifest

## Target repo

`Quantum-L9/l9-ci-debt-lsp`

## Branch

`wire/lsp-consume-compiled-rules`

## Purpose

Consume compiled rules from `l9-ci-debt-intelligence`, validate them, version-pin the consumed artifact, and prove diagnostics plus quick fixes through tests.

## Files

- `AGENTS.md`
- `.github/workflows/ci.yml`
- `package.json`
- `src/commands/refreshCorpus.ts`
- `server/corpus_compiler.py`
- `server/refresh_rules.py`
- `server/validate_compiled_rules.py`
- `server/rules_loader.py`
- `rules/compiled_rules.schema.json`
- `rules/compiled_rules.json`
- `rules/compiled_rules.lock.json`
- `fixtures/intelligence/outputs/compiled-rules/compiled_rules.json`
- `fixtures/intelligence/outputs/defense/astgrep/rules/CI-IMPORT-001.yaml`
- `fixtures/intelligence/outputs/offense/generated_invariants.yaml`
- `fixtures/bad-workflow.yml`
- `fixtures/good-workflow.yml`
- `fixtures/api-drift.py`
- `fixtures/doctrine-violation.py`
- `tests/test_compiled_rules_validation.py`
- `tests/test_diagnostics.py`
- `tests/test_code_actions.py`
- `docs/RULE_REFRESH.md`
- `docs/COMPILED_RULE_VALIDATION.md`
- `docs/DIAGNOSTICS_AND_CODE_ACTIONS.md`
- `CHANGE_SUMMARY.md`
- `VALIDATION.md`
- `RUNBOOK.md`
- `PR_BODY.md`


## Recursive optimization delta

- Added exact `rules_sha256` to `rules/compiled_rules.lock.json`.
- Aligned Intelligence fixture compiled-rules locations with the active packaged rule bundle.
- Changed CI Node dependency install from `npm ci` to `npm install` because this pack does not include `package-lock.json`.
- Set Jest to `--passWithNoTests` so TypeScript command validation does not fail when no TS tests are present in this PR.
