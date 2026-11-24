# Changelog

Notable changes to `l9-ci-debt-lsp`. The release engine reads the section that
matches the version in `pyproject.toml`, so headings are versioned and dated
exactly.

## 1.0.0 - 2026-11-24

First tagged release. The repository has carried version 1.0.0 since the LSP
architectural roadmap completed; this is the commit that makes that version
installable.

### Editor serving

- JSON-RPC and LSP lifecycle, document synchronization, workspace lifecycle
- immutable signed defense packs from `l9-ci-debt-intelligence`, with trusted
  signer resolution, Ed25519 verification, bounded extraction and per-member
  checksums
- incremental analysis behind a public SDK `AnalysisSession` boundary, with
  supersession, cancellation, freshness validation and stale-result suppression
- canonical diagnostics and bounded, explicitly approved quick fixes

### Effectiveness telemetry

- privacy-validated `l9.telemetry-event/v1` events, spooled locally and
  delivered as allowlisted HTTPS batches
- `policy/org-default.telemetry-policy.json`, the organization default that
  enables delivery (`user_opt_in` + `granted`) against the constellation ingress
- `telemetry-policy-apply` and `telemetry-policy-show`, which validate a policy
  document against the schema and the semantic rules before writing it
