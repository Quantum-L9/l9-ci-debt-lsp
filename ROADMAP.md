# L9 CI Debt LSP Roadmap
## LSP-P0 - Boundary cleanup
Status: Implemented
- remove corpus compiler
- remove mutable Intelligence output ingestion
- establish serving-only authority
- establish defense-pack consumer contract
- establish compatibility evaluation
- establish SDK schema federation
- establish architecture tests
## LSP-P1 - Pack protocol
Status: Implemented
- publication-manifest validation
- trusted-key registry
- checksum validation
- Ed25519 signature verification
- bounded safe archive extraction
- member checksum verification
- content-addressed immutable installation
- quarantine metadata
- atomic activation
- previous-known-good rollback
- compatibility reporting
- retired-pack rejection
- startup integrity recovery
## LSP-P2 - SDK incremental adapter
Status: Implemented
- public AnalysisSession protocol
- workspace sessions
- in-memory document overlays
- monotonic document versions
- cooperative cancellation
- deterministic bounded scheduling
- bounded dependency invalidation
- stale-result suppression
- latency measurement
- fail-closed incomplete analysis
- offline normal execution
## LSP-P3 - Diagnostic identity
Status: Implemented
- validate public SDK finding contracts
- preserve SDK finding IDs
- preserve canonical and provider rule IDs
- preserve document and pack lineage
- validate and clamp safe source ranges
- evidence links
- related information
- deterministic ordering
- deterministic de-duplication
- bounded diagnostic publication
- stale-safe publication
- incomplete-analysis diagnostics
- privacy-safe message redaction
## LSP-P4 - Bounded code actions
Status: Implemented
- immutable remediation-template consumption
- exact diagnostic and document-version binding
- deterministic current-document WorkspaceEdits
- edit range validation
- overlapping-edit conflict rejection
- protected-path exclusions
- bounded preview generation
- remediation provenance
- explicit user-approval boundary
- post-edit re-analysis contract
- no arbitrary command execution
- no autonomous multi-file repair
## LSP-P5 - Effectiveness loop
Status: Planned
- opt-in privacy-safe telemetry
- diagnostic dispositions
- false-positive dispositions
- quick-fix outcomes
- evaluation outcomes
- latency metrics
- canonical outcome events
