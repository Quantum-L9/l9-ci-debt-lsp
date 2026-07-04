# Diagnostics and Code Actions

## Diagnostics

Diagnostics are computed by `server/diagnostics.py` from the active compiled rule bundle. Rules match only files whose extension maps to the rule language.

Suppression uses each rule's `negative_patterns` within a local line window. This prevents fixed code from continuing to produce diagnostics.

## Code actions

`server/code_actions.py` emits edits only when the matching rule includes a complete `quick_fix` object.

Rules without safe quick fixes still surface an action to open documentation. Doctrine and structural API drift rules are intentionally not auto-edited unless Intelligence explicitly emits a safe edit.

## Test coverage

- `tests/test_diagnostics.py` proves bad fixtures produce diagnostics and good fixtures suppress them.
- `tests/test_code_actions.py` proves quick-fix rules produce edits while doctrine rules produce documentation actions only.
