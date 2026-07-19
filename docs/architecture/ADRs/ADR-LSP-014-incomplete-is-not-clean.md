# ADR-LSP-014: Incomplete analysis is not a clean result
- Status: Accepted
- Phase: LSP-P3
## Decision
An incomplete, failed, cancelled, or stale analysis cannot be represented as a
successful empty diagnostic set.
Incomplete and failed analysis produce an explicit limitation diagnostic when
publication remains current. Cancelled and stale results do not replace current
diagnostics.
