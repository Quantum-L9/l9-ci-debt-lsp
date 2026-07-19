# ADR-LSP-008: Retain previous-known-good pack state
- Status: Accepted
- Phase: LSP-P1
## Decision
Every successful activation preserves the former active pack as the
previous-known-good pack.
Rollback activates that exact immutable pack without recompilation or network
access.
