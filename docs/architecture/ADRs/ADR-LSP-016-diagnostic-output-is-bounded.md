# ADR-LSP-016: Diagnostic output is deterministic and bounded
- Status: Accepted
- Phase: LSP-P3
## Decision
Diagnostics are deterministically ordered and de-duplicated.
At most 200 finding diagnostics and one limitation diagnostic are published per
document. Overflow is disclosed explicitly and is never represented as complete
clean analysis.
