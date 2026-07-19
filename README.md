# Quantum-L9 CI Debt LSP
`l9-ci-debt-lsp` is the low-latency prevention edge of the Quantum-L9
constellation.
It serves deterministic diagnostics and bounded code actions in developer
editors using:
- immutable signed defense packs from `l9-ci-debt-intelligence`
- canonical evidence and finding semantics from `l9-ci-sdk`
- offline-first incremental document analysis
## Authority boundary
The LSP owns editor serving:
- JSON-RPC and LSP lifecycle
- document synchronization
- workspace lifecycle
- pack installation and activation
- diagnostics presentation
- bounded code actions
- cancellation and stale-result suppression
The LSP does not own:
- the canonical corpus
- corpus ingestion or mining
- rule generation
- pack compilation or signing
- CI governance
- policy promotion
- autonomous repair
## Phase status
The repository currently implements **LSP-P0: boundary cleanup**.
Available:
- defense-pack descriptor projection
- compatibility evaluation
- architecture enforcement
- minimal Python LSP server
- minimal VS Code client
Not yet available:
- cryptographic pack verification
- pack installation
- pack activation
- rollback
- SDK incremental analysis
- diagnostics
- code actions
- telemetry
These capabilities are implemented in subsequent phases.
## Development
```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
pytest
ruff check .
mypy src

Validate the phase capability contract:

l9-debt-lsp-contracts capabilities

Evaluate pack compatibility:

l9-debt-lsp-contracts evaluate-compatibility \
  --defense-pack tests/fixtures/packs/compatible-defense-pack.json \
  --compatibility tests/fixtures/packs/compatible-defense-pack.json \
  --platform linux-x86_64

VS Code client

cd vscode
npm install
npm run check
npm run compile

## Secure pack lifecycle
LSP-P1 implements the complete local defense-pack trust boundary:
```text
publication manifest
        ↓
schema validation
        ↓
trusted signer resolution
        ↓
archive SHA-256 verification
        ↓
Ed25519 verification
        ↓
bounded safe extraction
        ↓
member checksum verification
        ↓
pack schema validation
        ↓
compatibility and retirement checks
        ↓
immutable installation
        ↓
explicit atomic activation
        ↓
previous-known-good rollback

Installation and activation are separate operations.

l9-debt-lsp-contracts \
  --state-root ./var/lsp-state \
  install-pack \
  --manifest publication-manifest.json \
  --archive l9-debt-defense-1.0.0.tar.gz \
  --platform linux-x86_64
l9-debt-lsp-contracts \
  --state-root ./var/lsp-state \
  activate-pack \
  --pack-id pack_<sha256>
l9-debt-lsp-contracts \
  --state-root ./var/lsp-state \
  rollback-pack

A failed installation or activation never replaces the active or
previous-known-good pack.
## Incremental analysis runtime
LSP-P2 introduces a public SDK `AnalysisSession` boundary:
```text
editor document event
        ↓
workspace/document overlay
        ↓
strict version validation
        ↓
supersession and cancellation
        ↓
bounded deterministic scheduler
        ↓
SDK AnalysisSession
        ↓
freshness validation
        ↓
complete / incomplete / stale / cancelled result

The runtime guarantees:

* source overlays remain memory-only;
* document versions increase monotonically;
* newer edits supersede older work;
* stale results are discarded;
* incomplete analysis is not treated as PASS;
* normal analysis has no network dependency;
* dependency invalidation remains bounded;
* active-pack changes invalidate older work.

The default SDK adapter is fail-closed. Until a concrete public SDK binding is
configured, evaluations return incomplete with an explicit limitation.
## Canonical diagnostic publication
LSP-P3 projects canonical SDK findings into editor diagnostics:
```text
SDK analysis result
        ↓
public finding-contract validation
        ↓
identity and source-location validation
        ↓
privacy-safe presentation formatting
        ↓
evidence and related-information projection
        ↓
deterministic ordering and de-duplication
        ↓
document-version and pack freshness check
        ↓
LSP diagnostic publication

Each diagnostic preserves:

* SDK finding_id
* canonical rule ID
* provider rule ID
* document identity and version
* active pack ID and version
* corpus snapshot
* analysis request identity
* explicit limitations

Incomplete analysis produces an explicit limitation diagnostic. Stale or
cancelled results do not replace current diagnostics.
## Bounded code actions
LSP-P4 implements deterministic, explicitly approved quick fixes:
```text
canonical diagnostic
        ↓
active-pack remediation lookup
        ↓
diagnostic / pack / document-version binding
        ↓
protected-path validation
        ↓
edit-range and overlap validation
        ↓
bounded preview generation
        ↓
single-document WorkspaceEdit
        ↓
explicit editor-user approval
        ↓
new document version and re-analysis

Code actions cannot:

* execute commands;
* invoke a shell;
* run Git operations;
* install dependencies;
* edit protected paths;
* change multiple files;
* apply themselves automatically;
* use unbounded generated patches.

Every action contains provenance tying it to the exact finding, rule, template,
document version, defense pack, corpus snapshot, analysis request, and edit
digest.
## Privacy-safe effectiveness telemetry
LSP-P5 completes the feedback loop:
```text
diagnostic or quick-fix lifecycle
        ↓
explicit telemetry policy
        ↓
privacy validation
        ↓
canonical effectiveness event
        ↓
bounded local durable spool
        ↓
allowlisted HTTPS batch delivery
        ↓
Debt Intelligence aggregation

Telemetry defaults to disabled.

Supported modes:

* disabled
* local_only
* user_opt_in
* organization_controlled

Permitted event classes include:

* diagnostic shown and dismissed
* false-positive disposition
* quick-fix offered, applied, rejected, and outcome
* rule outcome
* latency bucket
* pack activation and rollback

Telemetry never contains:

* source content or snippets
* document or workspace URIs
* absolute or relative paths
* repository names or remotes
* branch names or commit hashes
* developer or machine identity
* credentials or secret values
* raw logs
* repository graphs
* raw corpus records

Telemetry failures never block diagnostics, code actions, pack activation, or
server startup.

Repository completion

Version 1.0.0 completes the LSP architectural roadmap:

LSP-P0  serving boundary
LSP-P1  secure pack lifecycle
LSP-P2  incremental SDK runtime
LSP-P3  canonical diagnostics
LSP-P4  bounded code actions
LSP-P5  privacy-safe effectiveness telemetry

