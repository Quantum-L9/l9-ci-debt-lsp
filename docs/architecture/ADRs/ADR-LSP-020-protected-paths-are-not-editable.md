# ADR-LSP-020: Security and governance paths are excluded from code actions
- Status: Accepted
- Phase: LSP-P4
## Decision
Code actions cannot modify Git metadata, workflow definitions, trust state,
pack state, activation state, retirement state, quarantine state, environment
files, credentials, private keys, or certificates.
