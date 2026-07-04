## Summary

PR3 wires `l9-ci-debt-lsp` to consume compiled rules from `l9-ci-debt-intelligence` through an explicit refresh command, validated compiled-rule schema, fixture Intelligence outputs, and version pinning via `rules/compiled_rules.lock.json`.

## Why

LSP should consume known-good rules produced by Intelligence, not drift into hardcoded local ghosts. This PR establishes the consumer side of the Resolver -> Intelligence -> LSP conveyor belt.

## Includes

- `AGENTS.md` repo operating contract
- rule refresh command: `server/refresh_rules.py`
- compiled-rule validation: `server/validate_compiled_rules.py`
- version pinning: `rules/compiled_rules.lock.json`
- fixture Intelligence compiled rules
- diagnostics tests
- code-action tests
- refreshed CI validation for rules and fixture refresh
- safer VS Code refresh command implementation using `spawn` instead of shell command interpolation

## Validation

Run locally:

```bash
python3.12 -m py_compile server/corpus_compiler.py server/refresh_rules.py server/validate_compiled_rules.py server/rules_loader.py server/diagnostics.py server/code_actions.py
python3.12 -m json.tool rules/compiled_rules.json >/dev/null
python3.12 -m json.tool rules/compiled_rules.lock.json >/dev/null
python3.12 -m json.tool rules/compiled_rules.schema.json >/dev/null
python3.12 server/validate_compiled_rules.py --rules rules/compiled_rules.json --lock rules/compiled_rules.lock.json
python3.12 server/refresh_rules.py --intelligence-outputs fixtures/intelligence/outputs --rules-out /tmp/l9-compiled-rules.json --lock-out /tmp/l9-compiled-rules.lock.json --expected-schema-version 1.0 --expected-artifact-name ci-debt-intelligence-compiled-rules --source-run-id local-fixture --source-sha local-fixture
python3.12 server/validate_compiled_rules.py --rules /tmp/l9-compiled-rules.json --lock /tmp/l9-compiled-rules.lock.json
python3.12 -m pytest tests/test_compiled_rules_validation.py tests/test_diagnostics.py tests/test_code_actions.py -q
npm ci
npm run compile
npm test
```

## Out of scope

- PR_Repair
- LLM-Router
- SDK/Core
- VSCE publishing
- npm publishing
- marketplace release
