# AGENTS.md - l9-ci-debt-lsp

## Mission

`l9-ci-debt-lsp` is the IDE-time prevention layer in the CI debt conveyor belt. It consumes compiled rule artifacts produced by `l9-ci-debt-intelligence` and exposes deterministic diagnostics and safe quick fixes before code reaches CI.

```text
l9-ci-debt-resolver -> l9-ci-debt-intelligence -> l9-ci-debt-lsp
```

## Repo Boundary

This repo may consume Intelligence outputs. It must not patch Resolver or Intelligence. It must not call upstream repositories during normal validation. Rule refresh is an explicit operator action or workflow step, not an implicit side effect of diagnostics.

## Accepted Inputs

The only accepted rule input is a compiled rules artifact matching `rules/compiled_rules.schema.json`.

Allowed local input locations:

- `rules/compiled_rules.json`
- `fixtures/intelligence/outputs/**` for tests and deterministic validation
- an operator-provided Intelligence artifact directory passed to `server/refresh_rules.py`

## Required Outputs

- `rules/compiled_rules.json` - active rule bundle consumed by the LSP server
- `rules/compiled_rules.lock.json` - version pin for the consumed Intelligence artifact
- LSP diagnostics from compiled rule patterns
- code actions only for rules with explicit quick-fix definitions

## Safety Rules

- Do not invent rule IDs.
- Do not silently accept malformed rule bundles.
- Do not generate quick fixes for doctrine or structural API drift unless the rule explicitly contains a safe edit.
- Do not auto-refresh rules at server startup.
- Do not depend on manual copying as the primary contract. Use the refresh command.
- Do not add PR_Repair, LLM-Router, SDK/Core, VSCE publishing, npm publishing, or marketplace workflow work in this PR.

## Validation Ladder

Run these before opening or merging PRs:

```bash
python3.12 -m py_compile server/corpus_compiler.py server/refresh_rules.py server/validate_compiled_rules.py server/rules_loader.py server/diagnostics.py server/code_actions.py
python3.12 -m json.tool rules/compiled_rules.json >/dev/null
python3.12 -m json.tool rules/compiled_rules.lock.json >/dev/null
python3.12 -m json.tool rules/compiled_rules.schema.json >/dev/null
python3.12 server/validate_compiled_rules.py --rules rules/compiled_rules.json --lock rules/compiled_rules.lock.json
python3.12 server/refresh_rules.py --intelligence-outputs fixtures/intelligence/outputs --rules-out /tmp/l9-compiled-rules.json --lock-out /tmp/l9-compiled-rules.lock.json --expected-schema-version 1.0 --expected-artifact-name ci-debt-intelligence-compiled-rules
python3.12 server/validate_compiled_rules.py --rules /tmp/l9-compiled-rules.json --lock /tmp/l9-compiled-rules.lock.json
python3.12 -m pytest tests/test_compiled_rules_validation.py tests/test_diagnostics.py tests/test_code_actions.py -q
npm install
npm run compile
npm test
```

If dependency installation is unavailable, report which validation layer was skipped and why. Never convert skipped checks into pass claims.
