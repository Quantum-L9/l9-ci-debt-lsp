# ADR-LSP-018: Code actions bind to an exact document and pack version
- Status: Accepted
- Phase: LSP-P4
## Decision
A code action is available only when its diagnostic document identity,
document version, rule-pack identity, and rule-pack version still match current
runtime state.
Stale diagnostics never produce edits.
