# Validation

## Pack-level validation performed during generation

```text
python py_compile for generated Python files: pass
json parse for compiled rules/schema/lock/package: pass
compiled rules validator on active fixture: pass
refresh from Intelligence fixture to /tmp: pass
compiled rules validator on refreshed /tmp output: pass
zip bundle created: pass
```

## Required local validation after applying to repo

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

## Unknowns

- Exact final PR2 Intelligence artifact path is not yet verified from a merged PR2. This pack accepts the preferred path and transition-compatible paths.
- Full pytest and npm validation require repo dependencies installed in the local checkout or CI runner.


## Recursive optimization delta

- Added exact `rules_sha256` to `rules/compiled_rules.lock.json`.
- Aligned Intelligence fixture compiled-rules locations with the active packaged rule bundle.
- Changed CI Node dependency install from `npm ci` to `npm install` because this pack does not include `package-lock.json`.
- Set Jest to `--passWithNoTests` so TypeScript command validation does not fail when no TS tests are present in this PR.
