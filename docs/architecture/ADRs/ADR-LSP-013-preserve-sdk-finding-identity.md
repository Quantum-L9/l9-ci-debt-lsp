# ADR-LSP-013: Preserve canonical SDK finding identity
- Status: Accepted
- Phase: LSP-P3
## Decision
The LSP preserves `finding_id`, `canonical_rule_id`, `provider_rule_id`,
source-location semantics, document identity, pack identity, and corpus
snapshot lineage.
The LSP may change editor severity presentation and message formatting, but it
does not create replacement finding IDs or reinterpret canonical rule meaning.
