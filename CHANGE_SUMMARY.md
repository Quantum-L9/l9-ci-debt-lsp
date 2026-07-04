# Change Summary

This PR3 pack makes `l9-ci-debt-lsp` consume compiled rules from `l9-ci-debt-intelligence` through an explicit refresh command and validated version pin.

## Added or replaced

- `AGENTS.md` repo operating contract
- `rules/compiled_rules.schema.json`
- `rules/compiled_rules.json`
- `rules/compiled_rules.lock.json`
- `server/corpus_compiler.py`
- `server/refresh_rules.py`
- `server/validate_compiled_rules.py`
- `server/rules_loader.py`
- `fixtures/intelligence/outputs/**`
- bad/good diagnostic fixtures
- diagnostics tests
- code-action tests
- compiled-rule validation tests
- refreshed CI workflow
- refresh command implementation update in `src/commands/refreshCorpus.ts`
- docs for refresh, validation, diagnostics, and code actions

## Out of scope

- PR_Repair integration
- LLM-Router
- VSCE publishing
- NPM publishing
- SDK/Core release automation
- marketplace publish


## Recursive optimization delta

- Added exact `rules_sha256` to `rules/compiled_rules.lock.json`.
- Aligned Intelligence fixture compiled-rules locations with the active packaged rule bundle.
- Changed CI Node dependency install from `npm ci` to `npm install` because this pack does not include `package-lock.json`.
- Set Jest to `--passWithNoTests` so TypeScript command validation does not fail when no TS tests are present in this PR.
