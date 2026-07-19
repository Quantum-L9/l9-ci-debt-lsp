# ADR-LSP-017: Code actions are bounded and deterministic
- Status: Accepted
- Phase: LSP-P4
## Decision
The LSP offers only deterministic template fixes and validated structural
rewrites published in the active immutable defense pack.
One action edits one open document, with at most 50 non-overlapping text edits.
Autonomous multi-file repair and unbounded generated patches remain prohibited.
