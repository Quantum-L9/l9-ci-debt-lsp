# ADR-LSP-022: Telemetry excludes source content and personal identity
- Status: Accepted
- Phase: LSP-P5
## Decision
Telemetry may include canonical technical identifiers needed for rule
effectiveness analysis.
It must not include source content, snippets, paths, document URIs, repository
identity, branch identity, commit identity, developer identity, machine
identity, credentials, raw logs, repository graphs, or raw corpus records.
