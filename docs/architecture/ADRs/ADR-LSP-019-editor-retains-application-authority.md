# ADR-LSP-019: The editor user retains edit application authority
- Status: Accepted
- Phase: LSP-P4
## Decision
The LSP constructs and previews a WorkspaceEdit but never applies it
autonomously.
The editor client and user retain the final approval boundary.
