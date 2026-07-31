# ADR-LSP-007: Installation and activation are separate operations
- Status: Accepted
- Phase: LSP-P1
## Decision
Successful installation places an immutable pack in content-addressed local
storage but does not activate it.
Activation requires an explicit pack identity and is performed atomically.
This prevents download, discovery, or installation processes from silently
changing editor behavior.
