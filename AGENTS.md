# AGENTS.md
## Repository identity
This repository is the Quantum-L9 low-latency prevention edge.
It serves immutable defense packs in editors. It is not a corpus, analytics,
rule-generation, repair, or governance repository.
## Required behavior
Agents working in this repository must:
- preserve document versions
- discard stale analysis results
- enforce latency budgets
- validate packs before activation
- preserve canonical finding identities
- preserve canonical rule identities
- preserve pack and corpus lineage
- retain previous-known-good packs
- reject incompatible packs
- keep normal diagnostics offline
- minimize and redact telemetry
- keep code actions bounded and deterministic
## Prohibited behavior
Agents must not:
- ingest the canonical corpus
- read Intelligence corpus internals
- mine fleet patterns
- generate authoritative prevention rules
- redefine canonical SDK schemas
- redefine canonical rule semantics
- silently recompile packs
- run full CI analysis per edit
- execute arbitrary commands from packs
- add autonomous multi-file repair
- mutate Git branches
- mutate source repositories
- treat incomplete analysis as PASS
## Required evidence
Changes affecting runtime behavior must include the relevant evidence:
- latency results
- pack compatibility results
- stale-result tests
- atomic activation tests
- rollback tests
- telemetry redaction tests
- identity-preservation tests
