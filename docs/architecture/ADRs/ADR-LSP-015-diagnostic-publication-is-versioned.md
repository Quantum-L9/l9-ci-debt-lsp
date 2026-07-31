# ADR-LSP-015: Diagnostic publication is version and pack aware
- Status: Accepted
- Phase: LSP-P3
## Decision
A diagnostic publication is committed only when its document version,
workspace generation, active pack, and analysis request still match current
runtime state.
Any mismatch causes the publication to be discarded.
