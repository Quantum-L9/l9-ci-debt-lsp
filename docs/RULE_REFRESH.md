# Rule Refresh Contract

## Purpose

`l9-ci-debt-lsp` consumes compiled rules produced by `l9-ci-debt-intelligence`. Refreshing rules is explicit and validated. The LSP server does not silently reach upstream repos while serving diagnostics.

## Canonical command

```bash
python server/refresh_rules.py \
  --intelligence-outputs ../l9-ci-debt-intelligence/outputs \
  --rules-out rules/compiled_rules.json \
  --lock-out rules/compiled_rules.lock.json \
  --expected-schema-version 1.0 \
  --expected-artifact-name ci-debt-intelligence-compiled-rules
```

## Fixture command

```bash
python server/refresh_rules.py \
  --intelligence-outputs fixtures/intelligence/outputs \
  --rules-out /tmp/l9-compiled-rules.json \
  --lock-out /tmp/l9-compiled-rules.lock.json \
  --expected-schema-version 1.0 \
  --expected-artifact-name ci-debt-intelligence-compiled-rules
```

## Accepted Intelligence output contract

Preferred:

```text
outputs/compiled-rules/compiled_rules.json
```

Compatibility during PR2 transition:

```text
outputs/defense/compiled_rules.json
outputs/defense/lsp/compiled_rules.json
outputs/rules/compiled_rules.json
outputs/defense/astgrep/rules/*.yaml + outputs/offense/generated_invariants.yaml
```

## Version pinning

Every refresh writes `rules/compiled_rules.lock.json`, including:

- `artifact_name`
- `producer`
- `source_run_id`
- `source_sha`
- `rules_sha256`
- `generated_at`
- `refreshed_at`
- `rule_count`

The lock file is the local evidence that LSP consumed a specific Intelligence artifact instead of hardcoded local ghosts.
