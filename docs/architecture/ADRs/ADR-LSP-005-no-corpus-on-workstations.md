# ADR-LSP-005: Full corpus data is never distributed to workstations
- Status: Accepted
- Phase: LSP-P0
## Decision
Defense packs contain only the minimum executable prevention representation and
required lineage metadata.
Raw corpus records, raw logs, repository identities, developer identities,
secret values, and full fleet graphs are prohibited.
