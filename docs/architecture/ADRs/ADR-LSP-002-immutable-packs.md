# ADR-LSP-002: Prevention packs are immutable and versioned
- Status: Accepted
- Phase: LSP-P0
## Decision
The LSP consumes explicit `l9.debt-defense/v1` pack versions.
Mutable `latest` artifacts, working-tree Intelligence outputs, and locally
compiled authoritative rules are not valid runtime authorities.
Installation and activation are separate operations. A pack must be verified
and compatible before it can be activated.
