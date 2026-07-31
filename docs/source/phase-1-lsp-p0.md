Phase 1 is LSP-P0: boundary cleanup and serving-system foundation.

This is a full repository overwrite. It removes the old corpus compiler, mutable Intelligence-output configuration, locally generated rules, and any runtime dependency on Intelligence corpus internals. The rebuilt repository becomes an offline-first editor-serving system that consumes immutable l9.debt-defense/v1 packs and delegates canonical analysis semantics to the SDK. repo-spec.yaml

Save this as build-phase-1.sh and run it from the root of Quantum-L9/l9-ci-debt-lsp.

#!/usr/bin/env bash
set -euo pipefail
###############################################################################
# Quantum-L9/l9-ci-debt-lsp
# Phase 1: LSP-P0 — Boundary Cleanup
#
# FULL OVERWRITE:
#   - Removes the legacy corpus compiler.
#   - Removes mutable Intelligence-output ingestion.
#   - Removes locally compiled authoritative rules.
#   - Rebuilds the repository as a serving-only LSP.
#   - Establishes contracts for immutable defense-pack consumption.
#
# This phase intentionally does not implement:
#   - signature verification
#   - archive installation
#   - active-pack switching
#   - SDK AnalysisSession execution
#   - production diagnostics
#   - code actions
#   - telemetry delivery
###############################################################################
fail() {
  printf 'LSP-P0: %s\n' "$*" >&2
  exit 1
}
require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}
require_command python3
[[ -d .git ]] || fail "run this script from the l9-ci-debt-lsp repository root"
REPOSITORY="Quantum-L9/l9-ci-debt-lsp"
SDK_REPOSITORY="Quantum-L9/l9-ci-sdk"
INTELLIGENCE_REPOSITORY="Quantum-L9/l9-ci-debt-intelligence"
printf 'LSP-P0: rebuilding %s as a serving-only repository\n' "${REPOSITORY}"
###############################################################################
# 1. Full overwrite
###############################################################################
find . -mindepth 1 -maxdepth 1 \
  ! -name '.git' \
  ! -name 'build-phase-1.sh' \
  -exec rm -rf {} +
mkdir -p \
  .github/workflows \
  .l9 \
  docs/architecture/ADRs \
  schemas/lsp \
  src/l9_debt_lsp/contracts \
  src/l9_debt_lsp/runtime \
  tests/architecture \
  tests/contracts \
  tests/runtime \
  tests/fixtures/packs \
  vscode/src
###############################################################################
# 2. Repository architecture
###############################################################################
cat > .l9/repo-spec.yaml <<'EOF'
schema: l9.repo-spec/v1
metadata:
  repository: Quantum-L9/l9-ci-debt-lsp
  repository_url: https://github.com/Quantum-L9/l9-ci-debt-lsp
  spec_path: .l9/repo-spec.yaml
  spec_version: 1.0.0
  status: authoritative
  phase: LSP-P0
  phase_name: boundary_cleanup
identity:
  name: l9-ci-debt-lsp
  constellation_role: low_latency_prevention_edge
  architectural_plane: editor_serving
  operating_model:
    - offline_first
    - low_latency
    - immutable_rule_pack_consumer
mission: >
  Serve deterministic diagnostics and bounded code actions in developer
  editors using validated prevention packs and the SDK incremental API.
ownership:
  owns:
    - LSP protocol
    - JSON-RPC lifecycle
    - VS Code client behavior
    - document synchronization
    - workspace lifecycle
    - diagnostics presentation
    - related information presentation
    - code action presentation
    - WorkspaceEdit construction
    - editor severity mapping
    - rule-pack installation
    - rule-pack activation
    - active pack cache
    - previous-known-good pack cache
    - incremental scheduling
    - debounce
    - cancellation
    - stale-result suppression
    - editor telemetry extensions
  does_not_own:
    - canonical fleet corpus
    - corpus ingestion
    - corpus normalization
    - corpus mining
    - prevention-rule generation
    - canonical SDK evidence schemas
    - canonical SDK finding schemas
    - canonical rule semantics
    - CI orchestration
    - policy promotion
    - autonomous multi-file repair
    - branch mutation
    - source repository mutation
dependency_contract:
  required:
    - Quantum-L9/l9-ci-sdk
  artifact_dependency:
    - Quantum-L9/l9-ci-debt-intelligence defense pack
  must_not_depend_on:
    - Quantum-L9/l9-ci-core
    - Quantum-L9/l9-ci-debt-resolver
    - Quantum-L9/PR_Repair
    - Debt Intelligence corpus internals
  invariant: >
    Normal diagnostics never require access to the canonical fleet corpus.
identity_preservation:
  must_preserve:
    - finding_id
    - canonical_rule_id
    - provider_rule_id
    - source_location
    - snapshot_or_document_identity
    - rule_pack_version
    - corpus_snapshot
  may_transform:
    - diagnostic severity presentation
    - editor message formatting
    - code action labels
  must_not_transform:
    - canonical rule semantics
    - finding fingerprint meaning
    - policy mode meaning
rule_pack_runtime:
  protocol: l9.debt-defense/v1
  responsibilities:
    - locate published pack
    - verify checksum
    - verify signature metadata
    - validate schema
    - validate SDK compatibility
    - install atomically
    - retain previous known-good pack
    - activate explicit version
    - report active version
  required_state:
    - pack_id
    - pack_version
    - corpus_snapshot
    - compiler_version
    - taxonomy_version
    - SDK_contract_version
    - compatibility_state
    - activation_time
  prohibited:
    - ingest raw corpus
    - mine patterns
    - generate authoritative rules
    - silently recompile rules
    - recompile from local telemetry
    - consume mutable Intelligence outputs
    - activate an unverified pack
incremental_analysis:
  SDK_interface: AnalysisSession
  operations:
    - open_workspace
    - open_document
    - update_document
    - evaluate_document
    - close_document
  requirements:
    - in-memory document overlay
    - document-version consistency
    - cancellation tokens
    - bounded dependency invalidation
    - no SQLite write per keystroke
    - no network dependency
    - partial parse support
    - deterministic diagnostics
  stale_result_rule: >
    Results produced for an older document version are discarded.
latency_budgets_ms:
  document_local:
    p50: 50
    p95: 200
  bounded_workspace:
    p95: 1000
  pack_activation:
    p95: 3000
schema_federation:
  references_SDK:
    - source-location
    - finding
    - evidence
  references_Intelligence:
    - defense-pack
  prohibition: >
    Canonical SDK findings and Intelligence corpus schemas are not duplicated.
diagnostics:
  deterministic_inputs:
    - document_text
    - document_version
    - workspace_capability_profile
    - active_rule_pack
    - SDK_incremental_semantics
  incomplete_analysis:
    behavior:
      - publish limitations
      - avoid false PASS
      - suppress unsafe fixes
      - retain known-good state where protocol-safe
code_actions:
  allowed:
    - deterministic template fix
    - validated structural rewrite
    - navigation
    - explanation
  prohibited:
    - autonomous multi-file repair
    - unbounded model-generated patches
    - protected-path mutation
    - arbitrary command execution
    - branch operations
    - Git mutation
telemetry:
  policy: opt_in_or_organization_controlled
  consumer: Quantum-L9/l9-ci-debt-intelligence
  emits:
    - rule_pack_version
    - canonical_rule_id
    - diagnostic_shown
    - diagnostic_dismissed
    - quick_fix_offered
    - quick_fix_applied
    - false_positive_disposition
    - latency_bucket
  excludes:
    - source content
    - secret values
    - absolute paths
    - developer identity
    - full repository graph
    - raw corpus records
security:
  packs:
    checksum_required: true
    signature_required: true
    atomic_installation: true
    previous_known_good_required: true
    incompatible_pack_behavior: reject_without_replacing_active_pack
  workspace:
    external_commands_from_rules: prohibited
    arbitrary_file_writes: prohibited
    network_by_default: false
  trust_boundaries:
    - Workspace content is untrusted.
    - Downloaded packs are untrusted until validated.
    - Telemetry is minimized and redacted.
phase:
  id: LSP-P0
  name: boundary_cleanup
  status: implemented
  includes:
    - authoritative ownership boundary
    - serving-only package foundation
    - defense-pack consumer contract
    - SDK schema-reference registry
    - compatibility policy
    - pack descriptor model
    - pack compatibility evaluator
    - architecture enforcement tests
    - minimal VS Code client foundation
    - minimal Python LSP server foundation
  excludes:
    - pack download
    - archive extraction
    - checksum verification implementation
    - cryptographic verification implementation
    - atomic activation
    - previous-known-good rollback implementation
    - SDK AnalysisSession implementation
    - diagnostic evaluation
    - production code actions
    - telemetry transport
removed_legacy_behavior:
  - corpus compiler
  - mutable Intelligence output ingestion
  - locally generated authoritative rules
  - Intelligence repository path configuration
  - refresh-corpus command
  - direct corpus access
EOF
cat > .l9/ownership.yaml <<'EOF'
schema: l9.ownership-spec/v1
repository: Quantum-L9/l9-ci-debt-lsp
lsp_owns:
  protocol:
    - JSON-RPC lifecycle
    - LSP capabilities
    - document synchronization
    - workspace synchronization
  serving:
    - runtime pack projection
    - diagnostics presentation
    - related information
    - severity mapping
    - bounded code actions
  lifecycle:
    - pack installation
    - pack activation
    - rollback
    - previous-known-good state
    - local active-pack cache
  runtime:
    - scheduling
    - cancellation
    - debounce
    - document version control
    - stale-result suppression
federated_from_sdk:
  - source-location
  - evidence
  - finding
  - finding identity
  - AnalysisSession semantics
consumed_from_intelligence:
  - l9.debt-defense/v1
  - publication manifest
  - compatibility matrix
  - signed pack archive
  - retirement metadata
prohibited:
  - canonical corpus ingestion
  - corpus mining
  - corpus normalization
  - recurrence analysis
  - co-occurrence analysis
  - effort analysis
  - prevention-rule compilation
  - rule promotion
  - policy promotion
  - Core governance mutation
  - arbitrary command execution
  - autonomous repair
  - Git mutation
  - source repository mutation
EOF
cat > .l9/defense-consumer-contract.yaml <<'EOF'
schema: l9.lsp-defense-consumer-contract/v1
metadata:
  repository: Quantum-L9/l9-ci-debt-lsp
  phase: LSP-P0
  status: authoritative
consumes:
  protocol: l9.debt-defense/v1
  owner: Quantum-L9/l9-ci-debt-intelligence
required_pack_fields:
  - pack_id
  - version
  - corpus_snapshot
  - analysis_run
  - compilation_id
  - compiler_version
  - taxonomy_version
  - SDK_contract_version
  - compatibility
  - rules
  - checksums
  - signature_metadata
  - limitations
validation_order:
  - parse_publication_manifest
  - validate_publication_manifest_schema
  - verify_archive_checksum
  - validate_signature_metadata
  - verify_detached_signature
  - safely_extract_archive
  - validate_defense_pack_schema
  - validate_compatibility
  - validate_runtime_rule_projection
  - stage_installation
  - activate_explicit_version
activation_invariant: >
  Installation never changes the active pack. Activation is a separate,
  explicit and atomic operation.
failure_invariant: >
  Rejected, corrupt, unsigned, incompatible, or incomplete packs never replace
  the active or previous-known-good pack.
compatibility:
  required:
    - SDK contract compatibility
    - LSP consumer contract compatibility
    - platform compatibility
    - supported runtime rule kinds
  unsupported_rule_behavior:
    - report unsupported rule identity
    - do not silently drop the rule
    - do not report successful full evaluation
    - preserve pack compatibility limitation
runtime_projection:
  input: immutable defense pack
  output: immutable runtime rule registry
  permitted_transformations:
    - deserialize rule representation
    - build indexes
    - cache normalized matcher structures
    - map severity for editor presentation
  prohibited_transformations:
    - change canonical rule meaning
    - generate new authoritative rules
    - alter canonical rule identity
    - infer missing corpus evidence
    - promote candidate rules
EOF
cat > .l9/sdk-schema-registry.json <<'EOF'
{
  "schema": "l9.lsp-sdk-schema-registry/v1",
  "sdk": {
    "repository": "Quantum-L9/l9-ci-sdk",
    "integration_contract": "l9.integration-contract/v1"
  },
  "references": {
    "source-location": {
      "uri": "l9://sdk/source-location/v1",
      "owner": "Quantum-L9/l9-ci-sdk"
    },
    "evidence": {
      "uri": "l9://sdk/evidence/v1",
      "owner": "Quantum-L9/l9-ci-sdk"
    },
    "finding": {
      "uri": "l9://sdk/finding/v1",
      "owner": "Quantum-L9/l9-ci-sdk"
    }
  },
  "policy": {
    "local_schema_copies_allowed": false,
    "private_sdk_imports_allowed": false,
    "unknown_sdk_contract_behavior": "reject"
  }
}
EOF
cat > .l9/compatibility-policy.yaml <<'EOF'
schema: l9.lsp-compatibility-policy/v1
consumer:
  contract: l9.lsp-defense-consumer/v1
  version: 1.0.0
sdk:
  accepted_contracts:
    - l9.integration-contract/v1
defense_pack:
  accepted_protocols:
    - l9.debt-defense/v1
runtime_rule_kinds:
  accepted:
    - ast_grep
    - sdk_architecture_contract
    - generated_invariant
  unknown_behavior: incompatible
platforms:
  accepted:
    - linux-x86_64
    - linux-arm64
    - darwin-x86_64
    - darwin-arm64
    - windows-x86_64
failure_behavior:
  invalid_schema: reject
  unsupported_protocol: reject
  incompatible_SDK: reject
  incompatible_LSP_contract: reject
  unsupported_platform: reject
  unsupported_rule_kind: reject
  incomplete_metadata: reject
active_pack_rule: >
  Compatibility failure never modifies active or previous-known-good state.
EOF
###############################################################################
# 3. Schemas
###############################################################################
cat > schemas/lsp/pack-descriptor.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/pack-descriptor/v1",
  "title": "L9 LSP Defense Pack Descriptor",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "pack_id",
    "pack_version",
    "protocol",
    "corpus_snapshot",
    "analysis_run",
    "compilation_id",
    "compiler_version",
    "taxonomy_version",
    "sdk_contract_version",
    "runtime_rule_kinds",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.lsp-pack-descriptor/v1"
    },
    "pack_id": {
      "type": "string",
      "pattern": "^pack_[0-9a-f]{64}$"
    },
    "pack_version": {
      "type": "string",
      "minLength": 1
    },
    "protocol": {
      "const": "l9.debt-defense/v1"
    },
    "corpus_snapshot": {
      "type": "string",
      "pattern": "^cs_[0-9a-f]{64}$"
    },
    "analysis_run": {
      "type": "string",
      "pattern": "^ar_[0-9a-f]{64}$"
    },
    "compilation_id": {
      "type": "string",
      "pattern": "^compile_[0-9a-f]{64}$"
    },
    "compiler_version": {
      "type": "string",
      "minLength": 1
    },
    "taxonomy_version": {
      "type": "string",
      "minLength": 1
    },
    "sdk_contract_version": {
      "type": "string",
      "minLength": 1
    },
    "runtime_rule_kinds": {
      "type": "array",
      "items": {
        "enum": [
          "ast_grep",
          "sdk_architecture_contract",
          "generated_invariant"
        ]
      },
      "uniqueItems": true
    },
    "limitations": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "uniqueItems": true
    }
  }
}
EOF
cat > schemas/lsp/pack-compatibility-result.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/pack-compatibility-result/v1",
  "title": "L9 LSP Pack Compatibility Result",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "status",
    "pack_id",
    "pack_version",
    "checks",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.lsp-pack-compatibility-result/v1"
    },
    "status": {
      "enum": [
        "compatible",
        "incompatible"
      ]
    },
    "pack_id": {
      "type": "string"
    },
    "pack_version": {
      "type": "string"
    },
    "checks": {
      "type": "object",
      "additionalProperties": {
        "type": "boolean"
      }
    },
    "limitations": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
EOF
cat > schemas/lsp/pack-installation-state.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/pack-installation-state/v1",
  "title": "L9 LSP Pack Installation State",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "pack_id",
    "pack_version",
    "state",
    "compatibility_state",
    "installed_path",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.pack-installation-state/v1"
    },
    "pack_id": {
      "type": "string",
      "pattern": "^pack_[0-9a-f]{64}$"
    },
    "pack_version": {
      "type": "string"
    },
    "state": {
      "enum": [
        "discovered",
        "validated",
        "verified",
        "staged",
        "installed",
        "active",
        "previous_known_good",
        "quarantined",
        "rejected"
      ]
    },
    "compatibility_state": {
      "enum": [
        "unknown",
        "compatible",
        "incompatible"
      ]
    },
    "installed_path": {
      "type": ["string", "null"]
    },
    "limitations": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
EOF
cat > schemas/lsp/runtime-rule.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/runtime-rule/v1",
  "title": "L9 LSP Runtime Rule",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "canonical_rule_id",
    "candidate_id",
    "kind",
    "pack_id",
    "pack_version",
    "corpus_snapshot",
    "match_contract",
    "action_contract",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.lsp-runtime-rule/v1"
    },
    "canonical_rule_id": {
      "type": "string",
      "minLength": 1
    },
    "candidate_id": {
      "type": "string",
      "pattern": "^candidate_[0-9a-f]{64}$"
    },
    "kind": {
      "enum": [
        "ast_grep",
        "sdk_architecture_contract",
        "generated_invariant"
      ]
    },
    "pack_id": {
      "type": "string",
      "pattern": "^pack_[0-9a-f]{64}$"
    },
    "pack_version": {
      "type": "string"
    },
    "corpus_snapshot": {
      "type": "string",
      "pattern": "^cs_[0-9a-f]{64}$"
    },
    "match_contract": {
      "type": "object"
    },
    "action_contract": {
      "type": "object"
    },
    "limitations": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
EOF
cat > schemas/lsp/server-capabilities.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/server-capabilities/v1",
  "title": "L9 LSP Server Capabilities",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "phase",
    "capabilities",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.lsp-server-capabilities/v1"
    },
    "phase": {
      "const": "LSP-P0"
    },
    "capabilities": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "pack_descriptor_validation",
        "pack_compatibility_evaluation",
        "pack_installation",
        "pack_activation",
        "diagnostics",
        "code_actions",
        "telemetry"
      ],
      "properties": {
        "pack_descriptor_validation": {
          "const": true
        },
        "pack_compatibility_evaluation": {
          "const": true
        },
        "pack_installation": {
          "const": false
        },
        "pack_activation": {
          "const": false
        },
        "diagnostics": {
          "const": false
        },
        "code_actions": {
          "const": false
        },
        "telemetry": {
          "const": false
        }
      }
    },
    "limitations": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
EOF
###############################################################################
# 4. Python package
###############################################################################
cat > pyproject.toml <<'EOF'
[build-system]
requires = ["hatchling>=1.25,<2"]
build-backend = "hatchling.build"
[project]
name = "l9-ci-debt-lsp"
version = "0.2.0"
description = "Offline-first LSP serving immutable Quantum-L9 debt-defense packs"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "Apache-2.0" }
authors = [
  { name = "Quantum-L9" }
]
dependencies = [
  "jsonschema>=4.23,<5",
  "pyyaml>=6.0,<7",
  "pygls>=1.3,<2"
]
[project.optional-dependencies]
dev = [
  "mypy>=1.11,<2",
  "pytest>=8.3,<9",
  "pytest-cov>=5,<7",
  "ruff>=0.6,<1"
]
[project.scripts]
l9-debt-lsp = "l9_debt_lsp.server:main"
l9-debt-lsp-contracts = "l9_debt_lsp.cli:main"
[tool.hatch.build.targets.wheel]
packages = ["src/l9_debt_lsp"]
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers"
[tool.ruff]
target-version = "py311"
line-length = 88
[tool.ruff.lint]
select = [
  "E",
  "F",
  "I",
  "B",
  "UP",
  "RUF"
]
[tool.mypy]
python_version = "3.11"
strict = true
packages = ["l9_debt_lsp"]
EOF
cat > src/l9_debt_lsp/__init__.py <<'EOF'
"""Quantum-L9 low-latency prevention edge."""
__version__ = "0.2.0"
EOF
cat > src/l9_debt_lsp/contracts/__init__.py <<'EOF'
"""Defense-pack consumer and compatibility contracts."""
EOF
cat > src/l9_debt_lsp/contracts/errors.py <<'EOF'
from __future__ import annotations
class ContractError(ValueError):
    """Base error for LSP consumer contract failures."""
class SchemaValidationError(ContractError):
    """A contract document failed JSON Schema validation."""
class PackCompatibilityError(ContractError):
    """A defense pack is incompatible with this LSP runtime."""
EOF
cat > src/l9_debt_lsp/contracts/canonical.py <<'EOF'
from __future__ import annotations
import hashlib
import json
from typing import Any
def canonical_json(value: Any) -> bytes:
    """Serialize a JSON-compatible value deterministically."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
def sha256_document(value: Any) -> str:
    """Return the SHA-256 hash of canonical JSON."""
    return hashlib.sha256(canonical_json(value)).hexdigest()
EOF
cat > src/l9_debt_lsp/contracts/models.py <<'EOF'
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
@dataclass(frozen=True)
class PackDescriptor:
    pack_id: str
    pack_version: str
    protocol: str
    corpus_snapshot: str
    analysis_run: str
    compilation_id: str
    compiler_version: str
    taxonomy_version: str
    sdk_contract_version: str
    runtime_rule_kinds: tuple[str, ...]
    limitations: tuple[str, ...]
    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.lsp-pack-descriptor/v1",
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "protocol": self.protocol,
            "corpus_snapshot": self.corpus_snapshot,
            "analysis_run": self.analysis_run,
            "compilation_id": self.compilation_id,
            "compiler_version": self.compiler_version,
            "taxonomy_version": self.taxonomy_version,
            "sdk_contract_version": self.sdk_contract_version,
            "runtime_rule_kinds": list(self.runtime_rule_kinds),
            "limitations": list(self.limitations),
        }
@dataclass(frozen=True)
class CompatibilityResult:
    status: str
    pack_id: str
    pack_version: str
    checks: dict[str, bool]
    limitations: tuple[str, ...]
    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.lsp-pack-compatibility-result/v1",
            "status": self.status,
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "checks": dict(sorted(self.checks.items())),
            "limitations": list(self.limitations),
        }
EOF
cat > src/l9_debt_lsp/contracts/schema.py <<'EOF'
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator, FormatChecker
from .errors import SchemaValidationError
class SchemaValidator:
    """Validate JSON documents against a Draft 2020-12 schema."""
    def __init__(self, schema_path: Path) -> None:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self._validator = Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        )
    def validate(self, document: dict[str, Any]) -> None:
        errors = sorted(
            self._validator.iter_errors(document),
            key=lambda error: list(error.absolute_path),
        )
        if not errors:
            return
        messages = []
        for error in errors:
            location = "/".join(str(item) for item in error.absolute_path)
            messages.append(
                f"{location or '<root>'}: {error.message}"
            )
        raise SchemaValidationError("; ".join(messages))
EOF
cat > src/l9_debt_lsp/contracts/descriptor.py <<'EOF'
from __future__ import annotations
from typing import Any
from .models import PackDescriptor
SUPPORTED_RULE_KINDS = frozenset(
    {
        "ast_grep",
        "sdk_architecture_contract",
        "generated_invariant",
    }
)
def descriptor_from_defense_pack(
    defense_pack: dict[str, Any],
) -> PackDescriptor:
    """Project an Intelligence defense pack into an LSP descriptor."""
    rules = defense_pack.get("rules")
    if not isinstance(rules, list):
        raise ValueError("defense pack rules must be an array")
    runtime_rule_kinds: set[str] = set()
    for rule in rules:
        if not isinstance(rule, dict):
            raise ValueError("defense pack rule must be an object")
        kind = rule.get("kind")
        if not isinstance(kind, str):
            raise ValueError("defense pack rule kind must be a string")
        runtime_rule_kinds.add(kind)
    limitations = defense_pack.get("limitations", [])
    if not isinstance(limitations, list):
        raise ValueError("defense pack limitations must be an array")
    return PackDescriptor(
        pack_id=str(defense_pack["pack_id"]),
        pack_version=str(defense_pack["version"]),
        protocol=str(defense_pack["schema_version"]),
        corpus_snapshot=str(defense_pack["corpus_snapshot"]),
        analysis_run=str(defense_pack["analysis_run"]),
        compilation_id=str(defense_pack["compilation_id"]),
        compiler_version=str(defense_pack["compiler_version"]),
        taxonomy_version=str(defense_pack["taxonomy_version"]),
        sdk_contract_version=str(
            defense_pack["SDK_contract_version"]
        ),
        runtime_rule_kinds=tuple(sorted(runtime_rule_kinds)),
        limitations=tuple(
            sorted(set(str(item) for item in limitations))
        ),
    )
EOF
cat > src/l9_debt_lsp/contracts/compatibility.py <<'EOF'
from __future__ import annotations
import platform
from typing import Any
from .models import CompatibilityResult, PackDescriptor
ACCEPTED_PROTOCOLS = frozenset({"l9.debt-defense/v1"})
ACCEPTED_SDK_CONTRACTS = frozenset({"l9.integration-contract/v1"})
ACCEPTED_RULE_KINDS = frozenset(
    {
        "ast_grep",
        "sdk_architecture_contract",
        "generated_invariant",
    }
)
def current_platform() -> str:
    """Return the normalized platform identity used by defense packs."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    system_names = {
        "linux": "linux",
        "darwin": "darwin",
        "windows": "windows",
    }
    machine_names = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "aarch64": "arm64",
        "arm64": "arm64",
    }
    normalized_system = system_names.get(system, system)
    normalized_machine = machine_names.get(machine, machine)
    return f"{normalized_system}-{normalized_machine}"
def evaluate_compatibility(
    *,
    descriptor: PackDescriptor,
    compatibility: dict[str, Any],
    platform_identity: str | None = None,
) -> CompatibilityResult:
    """Evaluate a defense pack without modifying local installation state."""
    platform_identity = platform_identity or current_platform()
    sdk = compatibility.get("sdk")
    lsp = compatibility.get("lsp")
    platforms = compatibility.get("platforms")
    checks = {
        "protocol_supported": descriptor.protocol in ACCEPTED_PROTOCOLS,
        "sdk_contract_supported": (
            descriptor.sdk_contract_version in ACCEPTED_SDK_CONTRACTS
        ),
        "sdk_matrix_present": isinstance(sdk, dict),
        "lsp_matrix_present": isinstance(lsp, dict),
        "platform_matrix_present": isinstance(platforms, list),
        "platform_supported": (
            isinstance(platforms, list)
            and platform_identity in platforms
        ),
        "runtime_rule_kinds_supported": set(
            descriptor.runtime_rule_kinds
        ).issubset(ACCEPTED_RULE_KINDS),
    }
    if isinstance(sdk, dict):
        checks["sdk_matrix_contract_matches"] = (
            sdk.get("contract") == descriptor.sdk_contract_version
        )
    else:
        checks["sdk_matrix_contract_matches"] = False
    if isinstance(lsp, dict):
        checks["lsp_consumer_contract_supported"] = (
            lsp.get("minimum_contract")
            == "l9.lsp-defense-consumer/v1"
        )
    else:
        checks["lsp_consumer_contract_supported"] = False
    failed = sorted(
        name for name, passed in checks.items() if not passed
    )
    return CompatibilityResult(
        status="compatible" if not failed else "incompatible",
        pack_id=descriptor.pack_id,
        pack_version=descriptor.pack_version,
        checks=checks,
        limitations=tuple(
            f"compatibility check failed: {name}"
            for name in failed
        ),
    )
EOF
cat > src/l9_debt_lsp/runtime/__init__.py <<'EOF'
"""Runtime serving abstractions for immutable defense packs."""
EOF
cat > src/l9_debt_lsp/runtime/state.py <<'EOF'
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
@dataclass(frozen=True)
class PackInstallationState:
    pack_id: str
    pack_version: str
    state: str
    compatibility_state: str
    installed_path: Path | None
    limitations: tuple[str, ...]
    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.pack-installation-state/v1",
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "state": self.state,
            "compatibility_state": self.compatibility_state,
            "installed_path": (
                self.installed_path.as_posix()
                if self.installed_path is not None
                else None
            ),
            "limitations": list(self.limitations),
        }
EOF
cat > src/l9_debt_lsp/runtime/capabilities.py <<'EOF'
from __future__ import annotations
from typing import Any
def phase_capabilities() -> dict[str, Any]:
    """Return the intentionally limited LSP-P0 capability surface."""
    return {
        "schema_version": "l9.lsp-server-capabilities/v1",
        "phase": "LSP-P0",
        "capabilities": {
            "pack_descriptor_validation": True,
            "pack_compatibility_evaluation": True,
            "pack_installation": False,
            "pack_activation": False,
            "diagnostics": False,
            "code_actions": False,
            "telemetry": False,
        },
        "limitations": [
            "LSP-P0 establishes boundaries and contracts only.",
            "Pack cryptographic verification is implemented in LSP-P1.",
            "Pack activation and rollback are implemented in LSP-P1.",
            "SDK incremental analysis is implemented in LSP-P2.",
        ],
    }
EOF
cat > src/l9_debt_lsp/cli.py <<'EOF'
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any, Sequence
from .contracts.compatibility import evaluate_compatibility
from .contracts.descriptor import descriptor_from_defense_pack
from .contracts.schema import SchemaValidator
from .runtime.capabilities import phase_capabilities
def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="l9-debt-lsp-contracts"
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )
    subparsers.add_parser("capabilities")
    validate = subparsers.add_parser("validate-descriptor")
    validate.add_argument("--document", type=Path, required=True)
    validate.add_argument(
        "--schema",
        type=Path,
        default=Path(
            "schemas/lsp/pack-descriptor.schema.json"
        ),
    )
    compatibility = subparsers.add_parser(
        "evaluate-compatibility"
    )
    compatibility.add_argument(
        "--defense-pack",
        type=Path,
        required=True,
    )
    compatibility.add_argument(
        "--compatibility",
        type=Path,
        required=True,
    )
    compatibility.add_argument("--platform")
    return parser
def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.command == "capabilities":
        print(
            json.dumps(
                phase_capabilities(),
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 0
    if arguments.command == "validate-descriptor":
        document = load_json(arguments.document)
        SchemaValidator(arguments.schema).validate(document)
        print(
            json.dumps(
                {
                    "status": "valid",
                    "schema_version": document.get(
                        "schema_version"
                    ),
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 0
    if arguments.command == "evaluate-compatibility":
        defense_pack = load_json(arguments.defense_pack)
        compatibility = load_json(arguments.compatibility)
        descriptor = descriptor_from_defense_pack(defense_pack)
        result = evaluate_compatibility(
            descriptor=descriptor,
            compatibility=compatibility,
            platform_identity=arguments.platform,
        )
        print(
            json.dumps(
                result.as_dict(),
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 0 if result.status == "compatible" else 2
    raise AssertionError("unreachable")
if __name__ == "__main__":
    raise SystemExit(main())
EOF
cat > src/l9_debt_lsp/server.py <<'EOF'
from __future__ import annotations
import json
from typing import Any
from pygls.server import LanguageServer
from .runtime.capabilities import phase_capabilities
SERVER_NAME = "l9-ci-debt-lsp"
SERVER_VERSION = "0.2.0"
server = LanguageServer(
    SERVER_NAME,
    SERVER_VERSION,
)
@server.feature("l9/serverCapabilities")
def l9_server_capabilities(
    _params: Any,
) -> dict[str, Any]:
    """Expose the phase capability contract to clients."""
    return phase_capabilities()
@server.command("l9.showServerCapabilities")
def show_server_capabilities(
    _arguments: list[Any],
) -> str:
    """Return serialized server capabilities."""
    return json.dumps(
        phase_capabilities(),
        sort_keys=True,
        separators=(",", ":"),
    )
def main() -> None:
    server.start_io()
if __name__ == "__main__":
    main()
EOF
###############################################################################
# 5. VS Code client
###############################################################################
cat > vscode/package.json <<'EOF'
{
  "name": "l9-ci-debt",
  "displayName": "L9 CI Debt",
  "description": "Deterministic editor diagnostics from immutable Quantum-L9 defense packs",
  "version": "0.2.0",
  "publisher": "quantum-l9",
  "license": "Apache-2.0",
  "engines": {
    "vscode": "^1.95.0"
  },
  "categories": [
    "Linters",
    "Programming Languages"
  ],
  "activationEvents": [
    "onLanguage:python",
    "onLanguage:yaml",
    "onLanguage:toml",
    "workspaceContains:.github/workflows/*"
  ],
  "main": "./dist/extension.js",
  "contributes": {
    "commands": [
      {
        "command": "l9CiDebt.showServerCapabilities",
        "title": "L9 CI Debt: Show Server Capabilities"
      }
    ],
    "configuration": {
      "title": "L9 CI Debt",
      "properties": {
        "l9CiDebt.server.pythonPath": {
          "type": "string",
          "default": "python3",
          "description": "Python interpreter used to launch the L9 CI Debt language server."
        },
        "l9CiDebt.server.module": {
          "type": "string",
          "default": "l9_debt_lsp.server",
          "description": "Python module containing the L9 CI Debt language server."
        },
        "l9CiDebt.pack.activeVersion": {
          "type": [
            "string",
            "null"
          ],
          "default": null,
          "description": "Explicit immutable defense-pack version. Activation is implemented in LSP-P1."
        },
        "l9CiDebt.telemetry.enabled": {
          "type": "boolean",
          "default": false,
          "description": "Enable minimized L9 telemetry after LSP-P5 is installed."
        }
      }
    }
  },
  "scripts": {
    "compile": "tsc -p ./",
    "check": "tsc -p ./ --noEmit"
  },
  "dependencies": {
    "vscode-languageclient": "^9.0.1"
  },
  "devDependencies": {
    "@types/node": "^22.10.0",
    "@types/vscode": "^1.95.0",
    "typescript": "^5.7.0"
  }
}
EOF
cat > vscode/tsconfig.json <<'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "lib": [
      "ES2022"
    ],
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "sourceMap": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true
  },
  "include": [
    "src/**/*.ts"
  ]
}
EOF
cat > vscode/src/extension.ts <<'EOF'
import * as vscode from "vscode";
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  TransportKind,
} from "vscode-languageclient/node";
let client: LanguageClient | undefined;
export async function activate(
  context: vscode.ExtensionContext,
): Promise<void> {
  const configuration = vscode.workspace.getConfiguration(
    "l9CiDebt",
  );
  const pythonPath = configuration.get<string>(
    "server.pythonPath",
    "python3",
  );
  const serverModule = configuration.get<string>(
    "server.module",
    "l9_debt_lsp.server",
  );
  const serverOptions: ServerOptions = {
    command: pythonPath,
    args: ["-m", serverModule],
    transport: TransportKind.stdio,
  };
  const clientOptions: LanguageClientOptions = {
    documentSelector: [
      { scheme: "file", language: "python" },
      { scheme: "file", language: "yaml" },
      { scheme: "file", language: "toml" },
    ],
    synchronize: {
      configurationSection: "l9CiDebt",
    },
  };
  client = new LanguageClient(
    "l9CiDebt",
    "L9 CI Debt",
    serverOptions,
    clientOptions,
  );
  context.subscriptions.push(
    vscode.commands.registerCommand(
      "l9CiDebt.showServerCapabilities",
      async () => {
        if (client === undefined) {
          await vscode.window.showErrorMessage(
            "L9 CI Debt language server is not running.",
          );
          return;
        }
        const capabilities = await client.sendRequest(
          "l9/serverCapabilities",
          {},
        );
        const document = await vscode.workspace.openTextDocument({
          language: "json",
          content: JSON.stringify(capabilities, null, 2),
        });
        await vscode.window.showTextDocument(document);
      },
    ),
  );
  await client.start();
}
export async function deactivate(): Promise<void> {
  if (client !== undefined) {
    await client.stop();
    client = undefined;
  }
}
EOF
###############################################################################
# 6. Tests
###############################################################################
cat > tests/fixtures/packs/compatible-defense-pack.json <<'EOF'
{
  "schema_version": "l9.debt-defense/v1",
  "pack_id": "pack_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "version": "1.0.0",
  "corpus_snapshot": "cs_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "analysis_run": "ar_cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "compilation_id": "compile_dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "compiler_version": "1.0.0",
  "taxonomy_version": "1.0.0",
  "SDK_contract_version": "l9.integration-contract/v1",
  "compatibility": {
    "schema_version": "l9.defense-compatibility/v1",
    "sdk": {
      "contract": "l9.integration-contract/v1",
      "minimum_version": "0.1.0",
      "maximum_version_exclusive": "2.0.0"
    },
    "core": {
      "minimum_contract": "l9.core-defense-consumer/v1"
    },
    "lsp": {
      "minimum_contract": "l9.lsp-defense-consumer/v1"
    },
    "platforms": [
      "linux-x86_64",
      "linux-arm64",
      "darwin-x86_64",
      "darwin-arm64",
      "windows-x86_64"
    ],
    "limitations": []
  },
  "rules": [
    {
      "canonical_rule_id": "l9.debt.example",
      "candidate_id": "candidate_eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      "kind": "ast_grep",
      "score": 4.5,
      "source_path": "rules/example.yaml",
      "source_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      "lineage": {
        "corpus_snapshot": "cs_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "analysis_run": "ar_cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "compilation_id": "compile_dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
        "recurrence_fingerprint": "1111111111111111111111111111111111111111111111111111111111111111"
      }
    }
  ],
  "checksums": {
    "rules/example.yaml": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
  },
  "signature_metadata": {
    "required": true,
    "algorithm": "Ed25519",
    "signed_value": "archive_sha256"
  },
  "limitations": []
}
EOF
cat > tests/architecture/test_serving_boundary.py <<'EOF'
from __future__ import annotations
import ast
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "src/l9_debt_lsp"
FORBIDDEN_MODULE_PREFIXES = (
    "l9_ci_core",
    "l9_ci_debt_resolver",
    "pr_repair",
)
FORBIDDEN_TERMS = (
    "corpus_compiler",
    "intelligenceoutputspath",
    "refreshcorpus",
    "outputs/corpus",
    "mine_patterns",
    "generate_authoritative_rules",
)
def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module)
    return modules
def test_runtime_does_not_import_forbidden_repositories() -> None:
    for path in SOURCE_ROOT.rglob("*.py"):
        for module in imported_modules(path):
            assert not module.startswith(
                FORBIDDEN_MODULE_PREFIXES
            ), f"{path} imports prohibited module {module}"
def test_removed_legacy_terms_do_not_exist_in_runtime() -> None:
    for path in SOURCE_ROOT.rglob("*.py"):
        content = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_TERMS:
            assert term not in content, (
                f"{path} contains prohibited legacy term {term}"
            )
def test_no_legacy_corpus_compiler_exists() -> None:
    assert not (ROOT / "server/corpus_compiler.py").exists()
    assert not (ROOT / "rules/compiled_rules.json").exists()
EOF
cat > tests/architecture/test_schema_federation.py <<'EOF'
from __future__ import annotations
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "schemas"
def test_no_sdk_schema_copies_are_present() -> None:
    prohibited_names = {
        "finding.schema.json",
        "evidence.schema.json",
        "source-location.schema.json",
        "corpus-record.schema.json",
        "corpus-event.schema.json",
    }
    present = {
        path.name
        for path in SCHEMA_ROOT.rglob("*.json")
    }
    assert present.isdisjoint(prohibited_names)
def test_lsp_only_owns_lsp_schemas() -> None:
    for path in SCHEMA_ROOT.rglob("*.json"):
        assert "schemas/lsp/" in path.as_posix()
EOF
cat > tests/contracts/test_descriptor.py <<'EOF'
from __future__ import annotations
import json
from pathlib import Path
from l9_debt_lsp.contracts.descriptor import (
    descriptor_from_defense_pack,
)
ROOT = Path(__file__).resolve().parents[2]
def test_descriptor_preserves_pack_lineage() -> None:
    pack = json.loads(
        (
            ROOT
            / "tests/fixtures/packs/compatible-defense-pack.json"
        ).read_text(encoding="utf-8")
    )
    descriptor = descriptor_from_defense_pack(pack)
    assert descriptor.pack_id == pack["pack_id"]
    assert descriptor.pack_version == pack["version"]
    assert descriptor.protocol == "l9.debt-defense/v1"
    assert descriptor.corpus_snapshot == pack["corpus_snapshot"]
    assert descriptor.analysis_run == pack["analysis_run"]
    assert descriptor.compilation_id == pack["compilation_id"]
    assert descriptor.sdk_contract_version == (
        "l9.integration-contract/v1"
    )
    assert descriptor.runtime_rule_kinds == ("ast_grep",)
EOF
cat > tests/contracts/test_compatibility.py <<'EOF'
from __future__ import annotations
import json
from pathlib import Path
from l9_debt_lsp.contracts.compatibility import (
    evaluate_compatibility,
)
from l9_debt_lsp.contracts.descriptor import (
    descriptor_from_defense_pack,
)
ROOT = Path(__file__).resolve().parents[2]
def load_pack() -> dict[str, object]:
    return json.loads(
        (
            ROOT
            / "tests/fixtures/packs/compatible-defense-pack.json"
        ).read_text(encoding="utf-8")
    )
def test_compatible_pack_is_accepted() -> None:
    pack = load_pack()
    descriptor = descriptor_from_defense_pack(pack)
    result = evaluate_compatibility(
        descriptor=descriptor,
        compatibility=pack["compatibility"],
        platform_identity="linux-x86_64",
    )
    assert result.status == "compatible"
    assert all(result.checks.values())
    assert result.limitations == ()
def test_unsupported_platform_is_incompatible() -> None:
    pack = load_pack()
    descriptor = descriptor_from_defense_pack(pack)
    result = evaluate_compatibility(
        descriptor=descriptor,
        compatibility=pack["compatibility"],
        platform_identity="unsupported-platform",
    )
    assert result.status == "incompatible"
    assert result.checks["platform_supported"] is False
def test_incompatible_sdk_contract_is_rejected() -> None:
    pack = load_pack()
    pack["SDK_contract_version"] = "l9.integration-contract/v999"
    descriptor = descriptor_from_defense_pack(pack)
    result = evaluate_compatibility(
        descriptor=descriptor,
        compatibility=pack["compatibility"],
        platform_identity="linux-x86_64",
    )
    assert result.status == "incompatible"
    assert result.checks["sdk_contract_supported"] is False
    assert result.checks["sdk_matrix_contract_matches"] is False
EOF
cat > tests/contracts/test_schema_validation.py <<'EOF'
from __future__ import annotations
import json
from pathlib import Path
import pytest
from l9_debt_lsp.contracts.descriptor import (
    descriptor_from_defense_pack,
)
from l9_debt_lsp.contracts.errors import SchemaValidationError
from l9_debt_lsp.contracts.schema import SchemaValidator
ROOT = Path(__file__).resolve().parents[2]
def test_pack_descriptor_schema_accepts_projected_pack() -> None:
    pack = json.loads(
        (
            ROOT
            / "tests/fixtures/packs/compatible-defense-pack.json"
        ).read_text(encoding="utf-8")
    )
    descriptor = descriptor_from_defense_pack(pack).as_dict()
    validator = SchemaValidator(
        ROOT / "schemas/lsp/pack-descriptor.schema.json"
    )
    validator.validate(descriptor)
def test_pack_descriptor_schema_rejects_invalid_identity() -> None:
    pack = json.loads(
        (
            ROOT
            / "tests/fixtures/packs/compatible-defense-pack.json"
        ).read_text(encoding="utf-8")
    )
    descriptor = descriptor_from_defense_pack(pack).as_dict()
    descriptor["pack_id"] = "mutable-latest"
    validator = SchemaValidator(
        ROOT / "schemas/lsp/pack-descriptor.schema.json"
    )
    with pytest.raises(SchemaValidationError):
        validator.validate(descriptor)
EOF
cat > tests/runtime/test_capabilities.py <<'EOF'
from __future__ import annotations
from l9_debt_lsp.runtime.capabilities import phase_capabilities
def test_phase_zero_capabilities_are_fail_closed() -> None:
    capabilities = phase_capabilities()
    assert capabilities["phase"] == "LSP-P0"
    assert (
        capabilities["capabilities"][
            "pack_descriptor_validation"
        ]
        is True
    )
    assert (
        capabilities["capabilities"][
            "pack_compatibility_evaluation"
        ]
        is True
    )
    assert (
        capabilities["capabilities"]["pack_installation"]
        is False
    )
    assert (
        capabilities["capabilities"]["pack_activation"]
        is False
    )
    assert capabilities["capabilities"]["diagnostics"] is False
    assert capabilities["capabilities"]["code_actions"] is False
    assert capabilities["capabilities"]["telemetry"] is False
EOF
###############################################################################
# 7. Documentation
###############################################################################
cat > docs/architecture/ADRs/ADR-LSP-001-serving-not-learning.md <<'EOF'
# ADR-LSP-001: LSP is a serving system, not a learning system
- Status: Accepted
- Phase: LSP-P0
## Decision
The LSP serves immutable prevention artifacts produced by Debt Intelligence.
It does not ingest the canonical corpus, normalize corpus events, calculate
fleet recurrence, mine patterns, generate authoritative rules, or promote
rules.
## Consequences
Normal editor operation requires no access to the Intelligence repository or
canonical fleet corpus.
The LSP may project a verified defense pack into an optimized in-memory runtime
representation, but that projection cannot change canonical rule semantics.
EOF
cat > docs/architecture/ADRs/ADR-LSP-002-immutable-packs.md <<'EOF'
# ADR-LSP-002: Prevention packs are immutable and versioned
- Status: Accepted
- Phase: LSP-P0
## Decision
The LSP consumes explicit `l9.debt-defense/v1` pack versions.
Mutable `latest` artifacts, working-tree Intelligence outputs, and locally
compiled authoritative rules are not valid runtime authorities.
Installation and activation are separate operations. A pack must be verified
and compatible before it can be activated.
EOF
cat > docs/architecture/ADRs/ADR-LSP-003-sdk-incremental-semantics.md <<'EOF'
# ADR-LSP-003: Incremental semantic computation belongs to the SDK
- Status: Accepted
- Phase: LSP-P0
## Decision
The LSP owns document lifecycle, scheduling, cancellation, debounce, stale
result suppression, and editor presentation.
The SDK owns canonical finding and evidence semantics and exposes incremental
analysis through `AnalysisSession`.
EOF
cat > docs/architecture/ADRs/ADR-LSP-004-compilation-upstream.md <<'EOF'
# ADR-LSP-004: Rule compilation occurs in Debt Intelligence
- Status: Accepted
- Phase: LSP-P0
## Decision
The historical LSP corpus compiler is removed.
Candidate extraction, scoring, rule generation, regression execution, pack
assembly, and signing occur upstream in Debt Intelligence.
EOF
cat > docs/architecture/ADRs/ADR-LSP-005-no-corpus-on-workstations.md <<'EOF'
# ADR-LSP-005: Full corpus data is never distributed to workstations
- Status: Accepted
- Phase: LSP-P0
## Decision
Defense packs contain only the minimum executable prevention representation and
required lineage metadata.
Raw corpus records, raw logs, repository identities, developer identities,
secret values, and full fleet graphs are prohibited.
EOF
cat > AGENTS.md <<'EOF'
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
EOF
cat > ROADMAP.md <<'EOF'
# L9 CI Debt LSP Roadmap
## LSP-P0 — Boundary cleanup
Status: Implemented
- remove corpus compiler
- remove mutable Intelligence output ingestion
- establish serving-only authority
- establish defense-pack consumer contract
- establish compatibility evaluation
- establish SDK schema federation
- establish architecture tests
## LSP-P1 — Pack protocol
Status: Planned
- publication-manifest validation
- checksum validation
- Ed25519 signature verification
- safe archive extraction
- content-addressed installation
- atomic activation
- previous-known-good rollback
- compatibility reporting
- retired-pack rejection
## LSP-P2 — SDK incremental adapter
Status: Planned
- AnalysisSession integration
- workspace sessions
- in-memory document overlays
- cancellation
- bounded invalidation
- stale-result suppression
## LSP-P3 — Diagnostic identity
Status: Planned
- preserve SDK finding IDs
- preserve canonical rule IDs
- evidence links
- related information
- deterministic ordering
- incomplete-analysis limitations
## LSP-P4 — Bounded code actions
Status: Planned
- validated quick fixes
- document-version checks
- edit conflict handling
- protected-path exclusions
- preview and provenance
- no arbitrary command execution
## LSP-P5 — Effectiveness loop
Status: Planned
- opt-in privacy-safe telemetry
- diagnostic dispositions
- false-positive dispositions
- quick-fix outcomes
- evaluation outcomes
- latency metrics
- canonical outcome events
EOF
cat > README.md <<'EOF'
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

EOF

###############################################################################

8. CI

###############################################################################

cat > .github/workflows/phase-1-boundary.yml <<‘EOF’
name: LSP-P0 Boundary

on:
pull_request:
push:
branches:
- main

permissions:
contents: read

jobs:
python:
runs-on: ubuntu-latest

steps:
  - name: Checkout
    uses: actions/checkout@v4
  - name: Python
    uses: actions/setup-python@v5
    with:
      python-version: "3.11"
      cache: pip
  - name: Install
    run: |
      python -m pip install --upgrade pip
      python -m pip install -e '.[dev]'
  - name: Architecture tests
    run: |
      pytest tests/architecture
  - name: Contract tests
    run: |
      pytest tests/contracts
  - name: Runtime tests
    run: |
      pytest tests/runtime
  - name: Ruff
    run: |
      ruff check .
  - name: Mypy
    run: |
      mypy src
  - name: Capabilities
    run: |
      l9-debt-lsp-contracts capabilities
  - name: Compatibility smoke test
    run: |
      l9-debt-lsp-contracts evaluate-compatibility \
        --defense-pack tests/fixtures/packs/compatible-defense-pack.json \
        --compatibility tests/fixtures/packs/compatible-defense-pack.json \
        --platform linux-x86_64

vscode:
runs-on: ubuntu-latest

defaults:
  run:
    working-directory: vscode
steps:
  - name: Checkout
    uses: actions/checkout@v4
  - name: Node
    uses: actions/setup-node@v4
    with:
      node-version: "22"
      cache: npm
      cache-dependency-path: vscode/package-lock.json
  - name: Install
    run: npm install
  - name: Type check
    run: npm run check
  - name: Compile
    run: npm run compile

EOF

###############################################################################

9. Repository hygiene

###############################################################################

cat > .gitignore <<‘EOF’

Python

pycache/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.venv/
dist/
build/
*.egg-info/

Node

vscode/node_modules/
vscode/dist/
vscode/*.vsix

Editors

.vscode/
.idea/

Runtime state

var/
.l9-runtime/
packs/
quarantine/

Secrets

*.pem
*.key
*.p12
*.pfx
.env
EOF

cat > LICENSE <<‘EOF’
Apache License
Version 2.0, January 2004
https://www.apache.org/licenses/
EOF

###############################################################################

10. Local validation

###############################################################################

python3 -m compileall -q src

python3 - <<‘PY’
from future import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

root = Path.cwd()

for schema_path in sorted((root / “schemas/lsp”).glob(”*.json”)):
schema = json.loads(schema_path.read_text(encoding=“utf-8”))
Draft202012Validator.check_schema(schema)

required = [
“.l9/repo-spec.yaml”,
“.l9/ownership.yaml”,
“.l9/defense-consumer-contract.yaml”,
“.l9/sdk-schema-registry.json”,
“.l9/compatibility-policy.yaml”,
“src/l9_debt_lsp/server.py”,
“src/l9_debt_lsp/contracts/compatibility.py”,
“vscode/src/extension.ts”,
“tests/architecture/test_serving_boundary.py”,
]

missing = [path for path in required if not (root / path).is_file()]
if missing:
raise SystemExit(f”missing required LSP-P0 files: {missing}”)

prohibited = [
“server/corpus_compiler.py”,
“rules/compiled_rules.json”,
]

remaining = [path for path in prohibited if (root / path).exists()]
if remaining:
raise SystemExit(f”legacy files survived overwrite: {remaining}”)

print(
json.dumps(
{
“schema_version”: “l9.phase-build-result/v1”,
“repository”: “Quantum-L9/l9-ci-debt-lsp”,
“phase”: “LSP-P0”,
“status”: “built”,
“mode”: “full-overwrite”,
“serving_boundary”: “enforced”,
“legacy_corpus_compiler”: “removed”,
“mutable_intelligence_outputs”: “removed”,
},
sort_keys=True,
separators=(”,”, “:”),
)
)
PY

printf ‘\n’
printf ‘LSP-P0 full overwrite complete.\n’
printf ‘\n’
printf ‘Implemented:\n’
printf ’  - serving-only repository authority\n’
printf ’  - immutable defense-pack consumer contract\n’
printf ’  - SDK schema federation\n’
printf ’  - pack descriptor projection\n’
printf ’  - fail-closed compatibility evaluation\n’
printf ’  - architecture boundary enforcement\n’
printf ’  - minimal Python LSP server\n’
printf ’  - minimal VS Code client\n’
printf ‘\n’
printf ‘Removed:\n’
printf ’  - corpus compiler\n’
printf ’  - mutable Intelligence-output ingestion\n’
printf ’  - locally generated authoritative rules\n’
printf ’  - refresh-corpus workflow\n’
printf ‘\n’
printf ‘Next phase: LSP-P1 — secure pack protocol, installation, activation, and rollback.\n’

:::
This phase makes the rebuilt repository authoritative from its first commit. There is no transitional corpus compiler and no compatibility path back to mutable `outputs/`; all later phases build on the immutable defense-pack boundary.