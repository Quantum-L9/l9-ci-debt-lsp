# Compiled Rule Validation

## Validator

```bash
python server/validate_compiled_rules.py --rules rules/compiled_rules.json --lock rules/compiled_rules.lock.json
```

## Required bundle shape

```json
{
  "schema_version": "1.0",
  "producer": "l9-ci-debt-intelligence",
  "artifact_name": "ci-debt-intelligence-compiled-rules",
  "generated_at": "...",
  "rules": []
}
```

## Required rule fields

- `id`
- `language`
- `topology`
- `severity`
- `pattern_type`
- `patterns`
- `negative_patterns`
- `message`
- `source`

## Validation checks

- Bundle is JSON object or legacy list.
- Object bundle contains `rules` array.
- Rule IDs are unique.
- Regex patterns compile.
- Severity is one of `error`, `warning`, `info`, `hint`.
- Pattern type is `regex`.
- Quick fixes include label, insertion regex, and insertion text.
- Lock file points to `l9-ci-debt-intelligence` and `ci-debt-intelligence-compiled-rules`.
