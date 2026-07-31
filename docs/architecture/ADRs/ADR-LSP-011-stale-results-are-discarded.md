# ADR-LSP-011: Stale analysis results are never published
- Status: Accepted
- Phase: LSP-P2
## Decision
An analysis result is stale when its document version, workspace generation,
active pack, or request identity no longer matches current runtime state.
Stale results are discarded. They are not converted to successful empty
diagnostics.
