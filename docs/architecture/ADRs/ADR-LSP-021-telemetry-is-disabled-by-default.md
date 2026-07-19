# ADR-LSP-021: Telemetry is disabled by default
- Status: Accepted
- Phase: LSP-P5
## Decision
Telemetry defaults to disabled.
Delivery requires explicit user consent or an organization-controlled policy.
Local-only telemetry is supported without network delivery.
Telemetry availability never gates diagnostics, code actions, pack activation,
or server startup.
