# ADR-LSP-012: Dependency invalidation is bounded
- Status: Accepted
- Phase: LSP-P2
## Decision
One document change may invalidate at most 250 dependent documents in the
immediate incremental path.
Overflow creates an explicit incomplete-analysis limitation and requires a
bounded workspace refresh. It never triggers an unbounded repository scan.
