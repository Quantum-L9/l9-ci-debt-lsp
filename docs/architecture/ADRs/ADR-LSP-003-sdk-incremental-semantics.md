# ADR-LSP-003: Incremental semantic computation belongs to the SDK
- Status: Accepted
- Phase: LSP-P0
## Decision
The LSP owns document lifecycle, scheduling, cancellation, debounce, stale
result suppression, and editor presentation.
The SDK owns canonical finding and evidence semantics and exposes incremental
analysis through `AnalysisSession`.
