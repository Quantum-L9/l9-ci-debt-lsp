# ADR-LSP-001: LSP is a serving system, not a learning system
- Status: Accepted
- Phase: LSP-P0
## Decision
The LSP serves immutable prevention artifacts produced by Debt Intelligence.
It does not ingest the canonical corpus, normalize corpus events, calculate
fleet recurrence, mine patterns, generate authoritative rules, or promote
rules.
## Consequences
Normal editor operation requires no access to the Intelligence repository or
canonical fleet corpus.
The LSP may project a verified defense pack into an optimized in-memory runtime
representation, but that projection cannot change canonical rule semantics.
