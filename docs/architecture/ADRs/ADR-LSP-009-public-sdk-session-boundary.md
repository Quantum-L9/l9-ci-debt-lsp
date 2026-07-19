# ADR-LSP-009: Incremental analysis uses a public SDK session boundary
- Status: Accepted
- Phase: LSP-P2
## Decision
The LSP integrates with SDK incremental semantics through the public
`AnalysisSession` protocol.
The LSP does not import SDK private modules or reconstruct SDK findings and
evidence.
A fail-closed unavailable adapter reports incomplete analysis rather than an
empty successful result.
