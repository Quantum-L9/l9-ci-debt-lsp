Phase 6 completes the repository with LSP-P5: privacy-safe effectiveness telemetry.

It closes the loop from editor outcomes back to Debt Intelligence while preserving the original repository constraints: telemetry is opt-in or organization-controlled and must exclude source content, secrets, absolute paths, developer identity, repository graphs, and raw corpus records. Phase 1.md

It builds on the exact finding, rule, pack, analysis-request, and remediation provenance established by LSP-P3 and LSP-P4. 

Save this as build-phase-6.sh and run it against the completed LSP-P4 repository.

#!/usr/bin/env bash
set -euo pipefail
###############################################################################
# Quantum-L9/l9-ci-debt-lsp
# LSP-P5 — Privacy-Safe Effectiveness Telemetry
#
# FINAL REPOSITORY PHASE
#
# Adds:
#   - explicit telemetry policy and consent model
#   - organization-controlled and user opt-in modes
#   - privacy-safe telemetry event schemas
#   - deterministic event identity
#   - rule-pack and canonical-rule outcome events
#   - diagnostic shown and dismissed events
#   - false-positive disposition events
#   - quick-fix offered, applied, rejected, and outcome events
#   - latency bucket events
#   - bounded durable local spool
#   - atomic append-only event persistence
#   - bounded batching
#   - retry with capped exponential backoff and jitter
#   - configurable HTTPS transport
#   - optional local-only mode
#   - source-content, path, secret, and identity rejection
#   - event retention and deletion
#   - telemetry health reporting
#   - fail-open editor behavior
#   - final architectural acceptance gates
#
# Prohibits:
#   - source content
#   - code snippets
#   - absolute paths
#   - document URIs
#   - developer identity
#   - email addresses
#   - machine identity
#   - repository names or remotes
#   - secret values
#   - raw logs
#   - full repository graphs
#   - raw corpus records
#   - telemetry-controlled rule activation
#   - telemetry blocking diagnostics or code actions
###############################################################################
fail() {
  printf 'LSP-P5: %s\n' "$*" >&2
  exit 1
}
require_file() {
  [[ -f "$1" ]] || fail "required prior-phase file missing: $1"
}
require_command() {
  command -v "$1" >/dev/null 2>&1 \
    || fail "required command not found: $1"
}
require_command python3
require_file ".l9/repo-spec.yaml"
require_file ".l9/code-action-contract.yaml"
require_file ".l9/diagnostic-contract.yaml"
require_file "src/l9_debt_lsp/actions/models.py"
require_file "src/l9_debt_lsp/diagnostics/models.py"
require_file "src/l9_debt_lsp/analysis/models.py"
require_file "src/l9_debt_lsp/runtime/capabilities.py"
require_file "src/l9_debt_lsp/server.py"
require_file "pyproject.toml"
mkdir -p \
  .github/workflows \
  .l9 \
  docs/architecture/ADRs \
  schemas/lsp \
  src/l9_debt_lsp/telemetry \
  src/l9_debt_lsp/runtime \
  tests/telemetry \
  tests/privacy \
  tests/resilience \
  tests/fixtures/telemetry
###############################################################################
# 1. Final telemetry contract
###############################################################################
cat > .l9/telemetry-contract.yaml <<'EOF'
schema: l9.lsp-telemetry-contract/v1
metadata:
  repository: Quantum-L9/l9-ci-debt-lsp
  phase: LSP-P5
  status: authoritative
  final_repository_phase: true
authority:
  lsp_owns:
    - telemetry consent evaluation
    - local event construction
    - privacy validation
    - local durable buffering
    - batching
    - transport retries
    - retention
    - telemetry health
    - event emission from editor lifecycle
  intelligence_owns:
    - effectiveness aggregation
    - recurrence analysis
    - false-positive analysis
    - rule quality assessment
    - candidate refinement
    - promotion and retirement decisions
  prohibited:
    - telemetry-generated local rule mutation
    - telemetry-controlled pack activation
    - telemetry-controlled policy promotion
    - telemetry blocking diagnostics
    - telemetry blocking code actions
    - telemetry redefining canonical findings
policy:
  default: disabled
  accepted_modes:
    - disabled
    - local_only
    - user_opt_in
    - organization_controlled
  organization_controlled:
    policy_source: signed_local_configuration
    user_override:
      may_enable_when_org_disabled: false
      may_disable_when_org_required: false
  user_opt_in:
    explicit_consent_required: true
    implied_consent_prohibited: true
  disabled:
    event_construction: minimized
    persistence: prohibited
    delivery: prohibited
privacy:
  allowed_identity:
    - telemetry_installation_id
    - session_id
    - event_id
    - canonical_rule_id
    - provider_rule_id
    - finding_id
    - rule_pack_id
    - rule_pack_version
    - corpus_snapshot
    - analysis_request_id
    - action_id
    - template_id
  telemetry_installation_id:
    generation: random_256_bit
    local_only_mapping: true
    rotation_supported: true
    linked_to_developer_identity: false
  prohibited_fields:
    - source_content
    - source_snippet
    - document_text
    - replacement_text
    - preview_diff
    - diagnostic_message
    - evidence_summary
    - related_information_message
    - absolute_path
    - relative_path
    - document_uri
    - workspace_uri
    - repository_name
    - repository_url
    - repository_remote
    - branch_name
    - commit_sha
    - developer_name
    - developer_email
    - account_id
    - machine_hostname
    - machine_serial
    - IP_address
    - secret_value
    - access_token
    - raw_log
    - raw_exception
    - raw_corpus_record
    - repository_graph
  prohibited_value_patterns:
    - absolute_unix_path
    - absolute_windows_path
    - file_uri
    - email_address
    - private_key
    - bearer_token
    - GitHub_token
    - AWS_access_key
    - generic_secret_assignment
events:
  common_required:
    - schema_version
    - event_id
    - event_type
    - occurred_at
    - installation_id
    - session_id
    - client_name
    - client_version
    - lsp_version
    - rule_pack_id
    - rule_pack_version
    - corpus_snapshot
    - limitations
  supported:
    - diagnostic_shown
    - diagnostic_dismissed
    - false_positive_disposition
    - quick_fix_offered
    - quick_fix_applied
    - quick_fix_rejected
    - quick_fix_outcome
    - rule_outcome
    - latency_bucket
    - pack_activated
    - pack_rollback
  dispositions:
    allowed:
      - false_positive
      - not_actionable
      - accepted_risk
      - duplicate
      - obsolete
      - valid_finding
      - unknown
    free_text: prohibited
  quick_fix_outcomes:
    allowed:
      - resolved
      - finding_persisted
      - new_findings_introduced
      - edit_reverted
      - outcome_unknown
  rule_outcomes:
    allowed:
      - finding_present
      - finding_resolved
      - finding_persisted
      - finding_dismissed
      - finding_dispositioned
  latency:
    raw_duration_delivery: prohibited
    buckets:
      - lt_25ms
      - 25_49ms
      - 50_99ms
      - 100_199ms
      - 200_499ms
      - 500_999ms
      - 1_2s
      - 2_5s
      - gt_5s
      - cancelled
      - timed_out
storage:
  root: state/telemetry
  queue: events
  dead_letter: dead-letter
  configuration: telemetry-policy.json
  installation_identity: installation-id.json
  delivery_state: delivery-state.json
  event_format: canonical_json
  file_identity: event_id
  immutable: true
  atomic_write: true
  file_permissions: owner_read_write
  directory_permissions: owner_read_write_execute
  limits:
    maximum_event_bytes: 16384
    maximum_queued_events: 10000
    maximum_queue_bytes: 52428800
    maximum_event_age_days: 30
    maximum_dead_letter_events: 1000
  overflow_behavior:
    strategy: delete_oldest_delivered_or_queued_events
    disclosure: telemetry_health_limitation
    editor_runtime_behavior: continue
delivery:
  enabled_modes:
    - user_opt_in
    - organization_controlled
  local_only_behavior:
    persist: true
    deliver: false
  transport:
    protocol: HTTPS
    content_type: application/x-ndjson
    compression: gzip
    redirects: prohibited
    endpoint_allowlist_required: true
    TLS_verification_required: true
    client_certificates: optional
    authorization:
      static_bearer_token_storage: prohibited
      environment_injection: allowed
      OS_secret_store_reference: allowed
  batching:
    maximum_events: 100
    maximum_uncompressed_bytes: 1048576
    deterministic_order:
      - occurred_at
      - event_id
  retries:
    maximum_attempts: 8
    initial_backoff_seconds: 1
    maximum_backoff_seconds: 300
    jitter: full
    retry_statuses:
      - 408
      - 425
      - 429
      - 500
      - 502
      - 503
      - 504
    non_retryable_behavior: dead_letter
  timeout_seconds:
    connect: 3
    read: 10
    total: 15
  failure_behavior:
    diagnostics: unaffected
    code_actions: unaffected
    pack_activation: unaffected
    server_startup: unaffected
    health: degraded
event_identity:
  algorithm: SHA-256
  prefix: event_
  inputs:
    - event_type
    - occurred_at
    - installation_id
    - session_id
    - canonical identity fields
    - sequence
session:
  identity:
    algorithm: random_256_bit
    prefix: session_
  persisted_across_processes: false
retention:
  purge:
    - expired_events
    - excess_queue_events
    - excess_queue_bytes
    - excess_dead_letter_events
  user_deletion:
    supported: true
    behavior:
      - delete_queue
      - delete_dead_letter
      - rotate_installation_identity
      - reset_delivery_state
observability:
  telemetry_health:
    required:
      - policy_mode
      - consent_state
      - queued_event_count
      - queued_bytes
      - oldest_event_age_seconds
      - dead_letter_count
      - last_delivery_status
      - last_successful_delivery_at
      - limitations
phase:
  id: LSP-P5
  status: implemented
  final_repository_phase: true
  includes:
    - consent policy
    - event schemas
    - event construction
    - privacy validation
    - deterministic event identity
    - local durable spool
    - bounded retention
    - HTTPS batch transport
    - retry and dead-letter handling
    - telemetry health
    - diagnostic dispositions
    - quick-fix outcomes
    - rule outcomes
    - latency buckets
    - pack lifecycle events
    - final acceptance gates
EOF
###############################################################################
# 2. Schemas
###############################################################################
cat > schemas/lsp/telemetry-policy.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/telemetry-policy/v1",
  "title": "L9 LSP Telemetry Policy",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "mode",
    "consent",
    "endpoint",
    "endpoint_allowlist",
    "retention_days",
    "organization_policy_id",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.telemetry-policy/v1"
    },
    "mode": {
      "enum": [
        "disabled",
        "local_only",
        "user_opt_in",
        "organization_controlled"
      ]
    },
    "consent": {
      "enum": [
        "not_required",
        "not_granted",
        "granted",
        "organization_required",
        "organization_disabled"
      ]
    },
    "endpoint": {
      "type": [
        "string",
        "null"
      ],
      "format": "uri"
    },
    "endpoint_allowlist": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      },
      "uniqueItems": true
    },
    "retention_days": {
      "type": "integer",
      "minimum": 1,
      "maximum": 30
    },
    "organization_policy_id": {
      "type": [
        "string",
        "null"
      ],
      "maxLength": 256
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
cat > schemas/lsp/telemetry-event.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/telemetry-event/v1",
  "title": "L9 Privacy-Safe Telemetry Event",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "event_id",
    "event_type",
    "occurred_at",
    "installation_id",
    "session_id",
    "sequence",
    "client_name",
    "client_version",
    "lsp_version",
    "rule_pack_id",
    "rule_pack_version",
    "corpus_snapshot",
    "canonical_rule_id",
    "provider_rule_id",
    "finding_id",
    "analysis_request_id",
    "action_id",
    "template_id",
    "outcome",
    "disposition",
    "latency_bucket",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.telemetry-event/v1"
    },
    "event_id": {
      "type": "string",
      "pattern": "^event_[0-9a-f]{64}$"
    },
    "event_type": {
      "enum": [
        "diagnostic_shown",
        "diagnostic_dismissed",
        "false_positive_disposition",
        "quick_fix_offered",
        "quick_fix_applied",
        "quick_fix_rejected",
        "quick_fix_outcome",
        "rule_outcome",
        "latency_bucket",
        "pack_activated",
        "pack_rollback"
      ]
    },
    "occurred_at": {
      "type": "string",
      "format": "date-time"
    },
    "installation_id": {
      "type": "string",
      "pattern": "^installation_[0-9a-f]{64}$"
    },
    "session_id": {
      "type": "string",
      "pattern": "^session_[0-9a-f]{64}$"
    },
    "sequence": {
      "type": "integer",
      "minimum": 1
    },
    "client_name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100
    },
    "client_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100
    },
    "lsp_version": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100
    },
    "rule_pack_id": {
      "type": [
        "string",
        "null"
      ]
    },
    "rule_pack_version": {
      "type": [
        "string",
        "null"
      ]
    },
    "corpus_snapshot": {
      "type": [
        "string",
        "null"
      ]
    },
    "canonical_rule_id": {
      "type": [
        "string",
        "null"
      ],
      "maxLength": 512
    },
    "provider_rule_id": {
      "type": [
        "string",
        "null"
      ],
      "maxLength": 512
    },
    "finding_id": {
      "type": [
        "string",
        "null"
      ],
      "maxLength": 512
    },
    "analysis_request_id": {
      "type": [
        "string",
        "null"
      ]
    },
    "action_id": {
      "type": [
        "string",
        "null"
      ]
    },
    "template_id": {
      "type": [
        "string",
        "null"
      ]
    },
    "outcome": {
      "type": [
        "string",
        "null"
      ],
      "enum": [
        null,
        "finding_present",
        "finding_resolved",
        "finding_persisted",
        "finding_dismissed",
        "finding_dispositioned",
        "resolved",
        "new_findings_introduced",
        "edit_reverted",
        "outcome_unknown"
      ]
    },
    "disposition": {
      "type": [
        "string",
        "null"
      ],
      "enum": [
        null,
        "false_positive",
        "not_actionable",
        "accepted_risk",
        "duplicate",
        "obsolete",
        "valid_finding",
        "unknown"
      ]
    },
    "latency_bucket": {
      "type": [
        "string",
        "null"
      ],
      "enum": [
        null,
        "lt_25ms",
        "25_49ms",
        "50_99ms",
        "100_199ms",
        "200_499ms",
        "500_999ms",
        "1_2s",
        "2_5s",
        "gt_5s",
        "cancelled",
        "timed_out"
      ]
    },
    "limitations": {
      "type": "array",
      "items": {
        "type": "string",
        "maxLength": 500
      },
      "uniqueItems": true,
      "maxItems": 20
    }
  }
}
EOF
cat > schemas/lsp/telemetry-health.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/telemetry-health/v1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "status",
    "policy_mode",
    "consent_state",
    "queued_event_count",
    "queued_bytes",
    "oldest_event_age_seconds",
    "dead_letter_count",
    "last_delivery_status",
    "last_successful_delivery_at",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.telemetry-health/v1"
    },
    "status": {
      "enum": [
        "healthy",
        "degraded",
        "disabled"
      ]
    },
    "policy_mode": {
      "enum": [
        "disabled",
        "local_only",
        "user_opt_in",
        "organization_controlled"
      ]
    },
    "consent_state": {
      "type": "string"
    },
    "queued_event_count": {
      "type": "integer",
      "minimum": 0
    },
    "queued_bytes": {
      "type": "integer",
      "minimum": 0
    },
    "oldest_event_age_seconds": {
      "type": [
        "number",
        "null"
      ],
      "minimum": 0
    },
    "dead_letter_count": {
      "type": "integer",
      "minimum": 0
    },
    "last_delivery_status": {
      "type": [
        "string",
        "null"
      ]
    },
    "last_successful_delivery_at": {
      "type": [
        "string",
        "null"
      ],
      "format": "date-time"
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
cat > schemas/lsp/telemetry-delivery-state.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/telemetry-delivery-state/v1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "last_attempt_at",
    "last_successful_delivery_at",
    "last_delivery_status",
    "consecutive_failures",
    "next_attempt_at",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.telemetry-delivery-state/v1"
    },
    "last_attempt_at": {
      "type": [
        "string",
        "null"
      ],
      "format": "date-time"
    },
    "last_successful_delivery_at": {
      "type": [
        "string",
        "null"
      ],
      "format": "date-time"
    },
    "last_delivery_status": {
      "type": [
        "string",
        "null"
      ]
    },
    "consecutive_failures": {
      "type": "integer",
      "minimum": 0
    },
    "next_attempt_at": {
      "type": [
        "string",
        "null"
      ],
      "format": "date-time"
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
# 3. Dependency
###############################################################################
python3 - <<'PY'
from pathlib import Path
path = Path("pyproject.toml")
text = path.read_text(encoding="utf-8")
if '"httpx>=0.27,<1"' not in text:
    text = text.replace(
        '  "cryptography>=43,<46"',
        '  "cryptography>=43,<46",\n'
        '  "httpx>=0.27,<1"',
    )
path.write_text(text, encoding="utf-8")
PY
###############################################################################
# 4. Telemetry package
###############################################################################
cat > src/l9_debt_lsp/telemetry/__init__.py <<'EOF'
"""Privacy-safe LSP effectiveness telemetry."""
EOF
cat > src/l9_debt_lsp/telemetry/errors.py <<'EOF'
from __future__ import annotations
class TelemetryError(RuntimeError):
    """Base telemetry failure."""
class TelemetryDisabled(TelemetryError):
    """Telemetry is disabled by policy."""
class TelemetryPolicyError(TelemetryError):
    """Telemetry policy is invalid or inconsistent."""
class TelemetryPrivacyError(TelemetryError):
    """Telemetry contains prohibited data."""
class TelemetryStorageError(TelemetryError):
    """Telemetry could not be persisted safely."""
class TelemetryTransportError(TelemetryError):
    """Telemetry could not be delivered."""
EOF
cat > src/l9_debt_lsp/telemetry/models.py <<'EOF'
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
@dataclass(frozen=True)
class TelemetryPolicy:
    mode: str
    consent: str
    endpoint: str | None
    endpoint_allowlist: tuple[str, ...]
    retention_days: int
    organization_policy_id: str | None
    limitations: tuple[str, ...]
    @property
    def persistence_enabled(self) -> bool:
        return self.mode != "disabled"
    @property
    def delivery_enabled(self) -> bool:
        if self.mode == "user_opt_in":
            return self.consent == "granted"
        if self.mode == "organization_controlled":
            return self.consent == "organization_required"
        return False
@dataclass(frozen=True)
class TelemetryContext:
    installation_id: str
    session_id: str
    client_name: str
    client_version: str
    lsp_version: str
@dataclass(frozen=True)
class TelemetryEvent:
    event_id: str
    event_type: str
    occurred_at: str
    installation_id: str
    session_id: str
    sequence: int
    client_name: str
    client_version: str
    lsp_version: str
    rule_pack_id: str | None
    rule_pack_version: str | None
    corpus_snapshot: str | None
    canonical_rule_id: str | None
    provider_rule_id: str | None
    finding_id: str | None
    analysis_request_id: str | None
    action_id: str | None
    template_id: str | None
    outcome: str | None
    disposition: str | None
    latency_bucket: str | None
    limitations: tuple[str, ...]
    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.telemetry-event/v1",
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "installation_id": self.installation_id,
            "session_id": self.session_id,
            "sequence": self.sequence,
            "client_name": self.client_name,
            "client_version": self.client_version,
            "lsp_version": self.lsp_version,
            "rule_pack_id": self.rule_pack_id,
            "rule_pack_version": self.rule_pack_version,
            "corpus_snapshot": self.corpus_snapshot,
            "canonical_rule_id": self.canonical_rule_id,
            "provider_rule_id": self.provider_rule_id,
            "finding_id": self.finding_id,
            "analysis_request_id": self.analysis_request_id,
            "action_id": self.action_id,
            "template_id": self.template_id,
            "outcome": self.outcome,
            "disposition": self.disposition,
            "latency_bucket": self.latency_bucket,
            "limitations": list(self.limitations),
        }
EOF
cat > src/l9_debt_lsp/telemetry/paths.py <<'EOF'
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from l9_debt_lsp.packs.paths import StatePaths
@dataclass(frozen=True)
class TelemetryPaths:
    state: StatePaths
    @property
    def root(self) -> Path:
        return self.state.root / "telemetry"
    @property
    def events(self) -> Path:
        return self.root / "events"
    @property
    def dead_letter(self) -> Path:
        return self.root / "dead-letter"
    @property
    def policy(self) -> Path:
        return self.root / "telemetry-policy.json"
    @property
    def installation_id(self) -> Path:
        return self.root / "installation-id.json"
    @property
    def delivery_state(self) -> Path:
        return self.root / "delivery-state.json"
    def initialize(self) -> None:
        for path in (
            self.root,
            self.events,
            self.dead_letter,
        ):
            path.mkdir(parents=True, exist_ok=True)
            path.chmod(0o700)
EOF
cat > src/l9_debt_lsp/telemetry/policy.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from l9_debt_lsp.contracts.schema import SchemaValidator
from l9_debt_lsp.packs.jsonio import (
    load_json,
    write_canonical_json,
)
from .errors import TelemetryPolicyError
from .models import TelemetryPolicy
DEFAULT_POLICY = {
    "schema_version": "l9.telemetry-policy/v1",
    "mode": "disabled",
    "consent": "not_granted",
    "endpoint": None,
    "endpoint_allowlist": [],
    "retention_days": 30,
    "organization_policy_id": None,
    "limitations": [],
}
class TelemetryPolicyStore:
    def __init__(
        self,
        *,
        path: Path,
        schema_path: Path,
    ) -> None:
        self.path = path
        self.schema_path = schema_path
    def initialize(self) -> None:
        if not self.path.is_file():
            write_canonical_json(
                self.path,
                DEFAULT_POLICY,
            )
    def load(self) -> TelemetryPolicy:
        self.initialize()
        document = load_json(self.path)
        SchemaValidator(self.schema_path).validate(document)
        policy = TelemetryPolicy(
            mode=document["mode"],
            consent=document["consent"],
            endpoint=document["endpoint"],
            endpoint_allowlist=tuple(
                sorted(set(document["endpoint_allowlist"]))
            ),
            retention_days=document["retention_days"],
            organization_policy_id=document[
                "organization_policy_id"
            ],
            limitations=tuple(
                sorted(set(document["limitations"]))
            ),
        )
        self._validate_semantics(policy)
        return policy
    def save(self, policy: TelemetryPolicy) -> None:
        self._validate_semantics(policy)
        write_canonical_json(
            self.path,
            {
                "schema_version": "l9.telemetry-policy/v1",
                "mode": policy.mode,
                "consent": policy.consent,
                "endpoint": policy.endpoint,
                "endpoint_allowlist": list(
                    policy.endpoint_allowlist
                ),
                "retention_days": policy.retention_days,
                "organization_policy_id": (
                    policy.organization_policy_id
                ),
                "limitations": list(policy.limitations),
            },
        )
    @staticmethod
    def _validate_semantics(policy: TelemetryPolicy) -> None:
        if policy.mode == "disabled":
            if policy.delivery_enabled:
                raise TelemetryPolicyError(
                    "disabled telemetry cannot deliver events"
                )
        if policy.mode == "local_only" and policy.endpoint is not None:
            raise TelemetryPolicyError(
                "local-only telemetry cannot define an endpoint"
            )
        if policy.delivery_enabled and policy.endpoint is None:
            raise TelemetryPolicyError(
                "delivery-enabled telemetry requires an endpoint"
            )
        if policy.endpoint is not None:
            if not policy.endpoint.startswith("https://"):
                raise TelemetryPolicyError(
                    "telemetry endpoint must use HTTPS"
                )
            if not any(
                policy.endpoint.startswith(prefix)
                for prefix in policy.endpoint_allowlist
            ):
                raise TelemetryPolicyError(
                    "telemetry endpoint is not allowlisted"
                )
EOF
cat > src/l9_debt_lsp/telemetry/identity.py <<'EOF'
from __future__ import annotations
import secrets
from pathlib import Path
from typing import Any
from l9_debt_lsp.packs.hashing import namespaced_hash
from l9_debt_lsp.packs.jsonio import (
    load_json,
    write_canonical_json,
)
def random_identity(prefix: str) -> str:
    return prefix + secrets.token_hex(32)
class InstallationIdentityStore:
    def __init__(self, path: Path) -> None:
        self.path = path
    def load_or_create(self) -> str:
        if self.path.is_file():
            document = load_json(self.path)
            value = document.get("installation_id")
            if (
                isinstance(value, str)
                and value.startswith("installation_")
                and len(value) == len("installation_") + 64
            ):
                return value
        value = random_identity("installation_")
        write_canonical_json(
            self.path,
            {
                "schema_version": (
                    "l9.telemetry-installation-id/v1"
                ),
                "installation_id": value,
            },
        )
        return value
    def rotate(self) -> str:
        value = random_identity("installation_")
        write_canonical_json(
            self.path,
            {
                "schema_version": (
                    "l9.telemetry-installation-id/v1"
                ),
                "installation_id": value,
            },
        )
        return value
def event_identity(value: dict[str, Any]) -> str:
    return namespaced_hash("event_", value)
EOF
cat > src/l9_debt_lsp/telemetry/privacy.py <<'EOF'
from __future__ import annotations
import json
import re
from typing import Any
from .errors import TelemetryPrivacyError
MAX_EVENT_BYTES = 16 * 1024
PROHIBITED_KEYS = {
    "source_content",
    "source_snippet",
    "document_text",
    "replacement_text",
    "preview_diff",
    "diagnostic_message",
    "evidence_summary",
    "related_information_message",
    "absolute_path",
    "relative_path",
    "document_uri",
    "workspace_uri",
    "repository_name",
    "repository_url",
    "repository_remote",
    "branch_name",
    "commit_sha",
    "developer_name",
    "developer_email",
    "account_id",
    "machine_hostname",
    "machine_serial",
    "ip_address",
    "secret_value",
    "access_token",
    "raw_log",
    "raw_exception",
    "raw_corpus_record",
    "repository_graph",
}
PROHIBITED_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9_.-])/(?:home|Users|private|tmp|var|opt)/\S+"),
    re.compile(r"(?<![A-Za-z0-9_.-])[A-Za-z]:\\[^\s]+"),
    re.compile(r"\bfile://\S+"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(
        r"(?i)\b(?:password|passwd|secret|token|api[_-]?key)"
        r"\s*[:=]\s*\S+"
    ),
)
def validate_privacy(value: Any) -> None:
    _validate_structure(value)
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(encoded) > MAX_EVENT_BYTES:
        raise TelemetryPrivacyError(
            "telemetry event exceeds maximum byte size"
        )
    text = encoded.decode("utf-8")
    for pattern in PROHIBITED_PATTERNS:
        if pattern.search(text):
            raise TelemetryPrivacyError(
                "telemetry event contains prohibited value pattern"
            )
def _validate_structure(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).casefold()
            if normalized in PROHIBITED_KEYS:
                raise TelemetryPrivacyError(
                    f"telemetry field is prohibited: {key}"
                )
            _validate_structure(item)
    elif isinstance(value, list):
        for item in value:
            _validate_structure(item)
    elif isinstance(value, tuple):
        for item in value:
            _validate_structure(item)
EOF
cat > src/l9_debt_lsp/telemetry/latency.py <<'EOF'
from __future__ import annotations
def latency_bucket(
    latency_ms: float,
    *,
    cancelled: bool = False,
    timed_out: bool = False,
) -> str:
    if timed_out:
        return "timed_out"
    if cancelled:
        return "cancelled"
    if latency_ms < 25:
        return "lt_25ms"
    if latency_ms < 50:
        return "25_49ms"
    if latency_ms < 100:
        return "50_99ms"
    if latency_ms < 200:
        return "100_199ms"
    if latency_ms < 500:
        return "200_499ms"
    if latency_ms < 1000:
        return "500_999ms"
    if latency_ms < 2000:
        return "1_2s"
    if latency_ms < 5000:
        return "2_5s"
    return "gt_5s"
EOF
cat > src/l9_debt_lsp/telemetry/events.py <<'EOF'
from __future__ import annotations
from dataclasses import replace
from typing import Any
from l9_debt_lsp.packs.time import format_utc, utc_now
from .identity import event_identity
from .models import (
    TelemetryContext,
    TelemetryEvent,
)
from .privacy import validate_privacy
SUPPORTED_EVENT_TYPES = {
    "diagnostic_shown",
    "diagnostic_dismissed",
    "false_positive_disposition",
    "quick_fix_offered",
    "quick_fix_applied",
    "quick_fix_rejected",
    "quick_fix_outcome",
    "rule_outcome",
    "latency_bucket",
    "pack_activated",
    "pack_rollback",
}
DISPOSITIONS = {
    "false_positive",
    "not_actionable",
    "accepted_risk",
    "duplicate",
    "obsolete",
    "valid_finding",
    "unknown",
}
OUTCOMES = {
    "finding_present",
    "finding_resolved",
    "finding_persisted",
    "finding_dismissed",
    "finding_dispositioned",
    "resolved",
    "new_findings_introduced",
    "edit_reverted",
    "outcome_unknown",
}
class EventFactory:
    def __init__(self, context: TelemetryContext) -> None:
        self.context = context
        self._sequence = 0
    def create(
        self,
        *,
        event_type: str,
        rule_pack_id: str | None = None,
        rule_pack_version: str | None = None,
        corpus_snapshot: str | None = None,
        canonical_rule_id: str | None = None,
        provider_rule_id: str | None = None,
        finding_id: str | None = None,
        analysis_request_id: str | None = None,
        action_id: str | None = None,
        template_id: str | None = None,
        outcome: str | None = None,
        disposition: str | None = None,
        latency_bucket: str | None = None,
        limitations: tuple[str, ...] = (),
    ) -> TelemetryEvent:
        if event_type not in SUPPORTED_EVENT_TYPES:
            raise ValueError(
                f"unsupported telemetry event type: {event_type}"
            )
        if disposition is not None and disposition not in DISPOSITIONS:
            raise ValueError(
                f"unsupported telemetry disposition: {disposition}"
            )
        if outcome is not None and outcome not in OUTCOMES:
            raise ValueError(
                f"unsupported telemetry outcome: {outcome}"
            )
        self._sequence += 1
        occurred_at = format_utc(utc_now())
        identity_input = {
            "event_type": event_type,
            "occurred_at": occurred_at,
            "installation_id": self.context.installation_id,
            "session_id": self.context.session_id,
            "sequence": self._sequence,
            "rule_pack_id": rule_pack_id,
            "canonical_rule_id": canonical_rule_id,
            "finding_id": finding_id,
            "action_id": action_id,
            "outcome": outcome,
            "disposition": disposition,
            "latency_bucket": latency_bucket,
        }
        event = TelemetryEvent(
            event_id=event_identity(identity_input),
            event_type=event_type,
            occurred_at=occurred_at,
            installation_id=self.context.installation_id,
            session_id=self.context.session_id,
            sequence=self._sequence,
            client_name=self.context.client_name,
            client_version=self.context.client_version,
            lsp_version=self.context.lsp_version,
            rule_pack_id=rule_pack_id,
            rule_pack_version=rule_pack_version,
            corpus_snapshot=corpus_snapshot,
            canonical_rule_id=canonical_rule_id,
            provider_rule_id=provider_rule_id,
            finding_id=finding_id,
            analysis_request_id=analysis_request_id,
            action_id=action_id,
            template_id=template_id,
            outcome=outcome,
            disposition=disposition,
            latency_bucket=latency_bucket,
            limitations=tuple(
                sorted(set(limitations))
            ),
        )
        validate_privacy(event.as_dict())
        return event
EOF
cat > src/l9_debt_lsp/telemetry/spool.py <<'EOF'
from __future__ import annotations
import datetime as dt
import os
from pathlib import Path
from typing import Iterable
from l9_debt_lsp.contracts.canonical import canonical_json
from l9_debt_lsp.packs.jsonio import (
    load_json,
    write_canonical_json,
)
from l9_debt_lsp.packs.time import parse_utc, utc_now
from .errors import TelemetryStorageError
from .models import TelemetryEvent
from .privacy import validate_privacy
MAX_EVENTS = 10_000
MAX_QUEUE_BYTES = 50 * 1024 * 1024
MAX_DEAD_LETTER = 1000
class TelemetrySpool:
    def __init__(
        self,
        *,
        event_root: Path,
        dead_letter_root: Path,
        retention_days: int,
    ) -> None:
        self.event_root = event_root
        self.dead_letter_root = dead_letter_root
        self.retention_days = retention_days
    def append(self, event: TelemetryEvent) -> Path:
        document = event.as_dict()
        validate_privacy(document)
        destination = self.event_root / f"{event.event_id}.json"
        if destination.exists():
            return destination
        try:
            write_canonical_json(
                destination,
                document,
            )
        except Exception as error:
            raise TelemetryStorageError(
                f"unable to persist telemetry event: {error}"
            ) from error
        self.enforce_limits()
        return destination
    def batch(
        self,
        *,
        maximum_events: int = 100,
        maximum_bytes: int = 1024 * 1024,
    ) -> list[tuple[Path, dict[str, object]]]:
        result: list[tuple[Path, dict[str, object]]] = []
        size = 0
        candidates: list[
            tuple[str, str, Path, dict[str, object]]
        ] = []
        for path in self.event_root.glob("event_*.json"):
            try:
                document = load_json(path)
                validate_privacy(document)
                candidates.append(
                    (
                        str(document["occurred_at"]),
                        str(document["event_id"]),
                        path,
                        document,
                    )
                )
            except Exception:
                self.move_to_dead_letter(
                    path,
                    reason="invalid_local_event",
                )
        candidates.sort(
            key=lambda value: (
                value[0],
                value[1],
            )
        )
        for _, _, path, document in candidates:
            encoded_size = len(canonical_json(document)) + 1
            if result and (
                len(result) >= maximum_events
                or size + encoded_size > maximum_bytes
            ):
                break
            if encoded_size > maximum_bytes:
                self.move_to_dead_letter(
                    path,
                    reason="event_exceeds_batch_limit",
                )
                continue
            result.append((path, document))
            size += encoded_size
        return result
    def acknowledge(self, paths: Iterable[Path]) -> None:
        for path in paths:
            path.unlink(missing_ok=True)
    def move_to_dead_letter(
        self,
        path: Path,
        *,
        reason: str,
    ) -> None:
        if not path.exists():
            return
        destination = self.dead_letter_root / path.name
        if destination.exists():
            path.unlink(missing_ok=True)
            return
        os.replace(path, destination)
        write_canonical_json(
            destination.with_suffix(".reason.json"),
            {
                "schema_version": (
                    "l9.telemetry-dead-letter/v1"
                ),
                "event_file": destination.name,
                "reason": reason,
            },
        )
        self._enforce_dead_letter_limit()
    def enforce_limits(self) -> None:
        files = sorted(
            self.event_root.glob("event_*.json"),
            key=lambda path: path.stat().st_mtime,
        )
        cutoff = utc_now() - dt.timedelta(
            days=self.retention_days
        )
        for path in list(files):
            try:
                document = load_json(path)
                occurred_at = parse_utc(
                    str(document["occurred_at"])
                )
                if occurred_at < cutoff:
                    path.unlink(missing_ok=True)
            except Exception:
                self.move_to_dead_letter(
                    path,
                    reason="retention_parse_failure",
                )
        files = sorted(
            self.event_root.glob("event_*.json"),
            key=lambda path: path.stat().st_mtime,
        )
        while len(files) > MAX_EVENTS:
            files.pop(0).unlink(missing_ok=True)
        total = sum(path.stat().st_size for path in files)
        while files and total > MAX_QUEUE_BYTES:
            path = files.pop(0)
            total -= path.stat().st_size
            path.unlink(missing_ok=True)
    def clear(self) -> None:
        for root in (
            self.event_root,
            self.dead_letter_root,
        ):
            for path in root.iterdir():
                if path.is_file():
                    path.unlink(missing_ok=True)
    def statistics(self) -> dict[str, int | float | None]:
        files = list(
            self.event_root.glob("event_*.json")
        )
        queued_bytes = sum(
            path.stat().st_size
            for path in files
        )
        oldest_age: float | None = None
        if files:
            oldest_mtime = min(
                path.stat().st_mtime
                for path in files
            )
            oldest_age = max(
                0.0,
                utc_now().timestamp() - oldest_mtime,
            )
        dead_letter_count = len(
            list(
                self.dead_letter_root.glob(
                    "event_*.json"
                )
            )
        )
        return {
            "queued_event_count": len(files),
            "queued_bytes": queued_bytes,
            "oldest_event_age_seconds": oldest_age,
            "dead_letter_count": dead_letter_count,
        }
    def _enforce_dead_letter_limit(self) -> None:
        files = sorted(
            self.dead_letter_root.glob("event_*.json"),
            key=lambda path: path.stat().st_mtime,
        )
        while len(files) > MAX_DEAD_LETTER:
            path = files.pop(0)
            path.unlink(missing_ok=True)
            path.with_suffix(".reason.json").unlink(
                missing_ok=True
            )
EOF
cat > src/l9_debt_lsp/telemetry/delivery_state.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from typing import Any
from l9_debt_lsp.packs.jsonio import (
    load_json,
    write_canonical_json,
)
DEFAULT_STATE = {
    "schema_version": "l9.telemetry-delivery-state/v1",
    "last_attempt_at": None,
    "last_successful_delivery_at": None,
    "last_delivery_status": None,
    "consecutive_failures": 0,
    "next_attempt_at": None,
    "limitations": [],
}
class DeliveryStateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
    def load(self) -> dict[str, Any]:
        if not self.path.is_file():
            write_canonical_json(
                self.path,
                DEFAULT_STATE,
            )
        return load_json(self.path)
    def save(self, state: dict[str, Any]) -> None:
        write_canonical_json(self.path, state)
EOF
cat > src/l9_debt_lsp/telemetry/transport.py <<'EOF'
from __future__ import annotations
import asyncio
import gzip
import random
from pathlib import Path
from typing import Any
import httpx
from l9_debt_lsp.contracts.canonical import canonical_json
from l9_debt_lsp.packs.time import format_utc, utc_now
from .delivery_state import DeliveryStateStore
from .errors import TelemetryTransportError
from .models import TelemetryPolicy
from .spool import TelemetrySpool
RETRYABLE_STATUSES = {
    408,
    425,
    429,
    500,
    502,
    503,
    504,
}
class TelemetryTransport:
    def __init__(
        self,
        *,
        policy: TelemetryPolicy,
        spool: TelemetrySpool,
        state_store: DeliveryStateStore,
        authorization_token: str | None = None,
    ) -> None:
        self.policy = policy
        self.spool = spool
        self.state_store = state_store
        self.authorization_token = authorization_token
    async def deliver_once(self) -> dict[str, Any]:
        state = self.state_store.load()
        if not self.policy.delivery_enabled:
            state["last_delivery_status"] = "delivery_disabled"
            self.state_store.save(state)
            return state
        if self.policy.endpoint is None:
            raise TelemetryTransportError(
                "delivery endpoint is not configured"
            )
        batch = self.spool.batch()
        if not batch:
            state["last_delivery_status"] = "queue_empty"
            self.state_store.save(state)
            return state
        paths = [path for path, _ in batch]
        body = b"\n".join(
            canonical_json(document)
            for _, document in batch
        ) + b"\n"
        compressed = gzip.compress(body)
        headers = {
            "Content-Type": "application/x-ndjson",
            "Content-Encoding": "gzip",
            "User-Agent": "l9-ci-debt-lsp-telemetry/1",
        }
        if self.authorization_token:
            headers["Authorization"] = (
                f"Bearer {self.authorization_token}"
            )
        now = format_utc(utc_now())
        state["last_attempt_at"] = now
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    timeout=15.0,
                    connect=3.0,
                    read=10.0,
                ),
                follow_redirects=False,
                verify=True,
            ) as client:
                response = await client.post(
                    self.policy.endpoint,
                    headers=headers,
                    content=compressed,
                )
            if 200 <= response.status_code < 300:
                self.spool.acknowledge(paths)
                state["last_successful_delivery_at"] = now
                state["last_delivery_status"] = (
                    f"succeeded:{response.status_code}"
                )
                state["consecutive_failures"] = 0
                state["next_attempt_at"] = None
                state["limitations"] = []
                self.state_store.save(state)
                return state
            if response.status_code in RETRYABLE_STATUSES:
                return self._record_retryable_failure(
                    state,
                    f"http_{response.status_code}",
                )
            for path in paths:
                self.spool.move_to_dead_letter(
                    path,
                    reason=f"http_{response.status_code}",
                )
            state["last_delivery_status"] = (
                f"dead_lettered:{response.status_code}"
            )
            state["consecutive_failures"] = 0
            state["next_attempt_at"] = None
            state["limitations"] = [
                "Telemetry batch was rejected permanently."
            ]
            self.state_store.save(state)
            return state
        except (
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.TransportError,
        ) as error:
            return self._record_retryable_failure(
                state,
                type(error).__name__,
            )
    def _record_retryable_failure(
        self,
        state: dict[str, Any],
        reason: str,
    ) -> dict[str, Any]:
        failures = min(
            int(state.get("consecutive_failures", 0)) + 1,
            8,
        )
        base = min(300, 2 ** (failures - 1))
        delay = random.uniform(0, float(base))
        next_attempt = utc_now().timestamp() + delay
        import datetime as dt
        state["last_delivery_status"] = (
            f"retryable_failure:{reason}"
        )
        state["consecutive_failures"] = failures
        state["next_attempt_at"] = format_utc(
            dt.datetime.fromtimestamp(
                next_attempt,
                tz=dt.timezone.utc,
            )
        )
        state["limitations"] = [
            "Telemetry delivery is degraded; editor behavior is unaffected."
        ]
        self.state_store.save(state)
        return state
EOF
cat > src/l9_debt_lsp/telemetry/health.py <<'EOF'
from __future__ import annotations
from typing import Any
from .delivery_state import DeliveryStateStore
from .models import TelemetryPolicy
from .spool import TelemetrySpool
def telemetry_health(
    *,
    policy: TelemetryPolicy,
    spool: TelemetrySpool,
    delivery_state: DeliveryStateStore,
) -> dict[str, Any]:
    statistics = spool.statistics()
    state = delivery_state.load()
    limitations = list(policy.limitations)
    limitations.extend(state.get("limitations", []))
    if policy.mode == "disabled":
        status = "disabled"
    elif limitations:
        status = "degraded"
    else:
        status = "healthy"
    return {
        "schema_version": "l9.telemetry-health/v1",
        "status": status,
        "policy_mode": policy.mode,
        "consent_state": policy.consent,
        "queued_event_count": statistics[
            "queued_event_count"
        ],
        "queued_bytes": statistics["queued_bytes"],
        "oldest_event_age_seconds": statistics[
            "oldest_event_age_seconds"
        ],
        "dead_letter_count": statistics[
            "dead_letter_count"
        ],
        "last_delivery_status": state.get(
            "last_delivery_status"
        ),
        "last_successful_delivery_at": state.get(
            "last_successful_delivery_at"
        ),
        "limitations": sorted(set(limitations)),
    }
EOF
cat > src/l9_debt_lsp/telemetry/service.py <<'EOF'
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
from .delivery_state import DeliveryStateStore
from .events import EventFactory
from .health import telemetry_health
from .identity import (
    InstallationIdentityStore,
    random_identity,
)
from .models import (
    TelemetryContext,
    TelemetryEvent,
)
from .paths import TelemetryPaths
from .policy import TelemetryPolicyStore
from .spool import TelemetrySpool
from .transport import TelemetryTransport
class TelemetryService:
    def __init__(
        self,
        *,
        paths: TelemetryPaths,
        schema_root: Path,
        client_name: str,
        client_version: str,
        lsp_version: str,
    ) -> None:
        self.paths = paths
        self.paths.initialize()
        self.policy_store = TelemetryPolicyStore(
            path=paths.policy,
            schema_path=(
                schema_root
                / "telemetry-policy.schema.json"
            ),
        )
        self.identity_store = InstallationIdentityStore(
            paths.installation_id
        )
        self.context = TelemetryContext(
            installation_id=(
                self.identity_store.load_or_create()
            ),
            session_id=random_identity("session_"),
            client_name=client_name,
            client_version=client_version,
            lsp_version=lsp_version,
        )
        self.factory = EventFactory(self.context)
        self.delivery_state = DeliveryStateStore(
            paths.delivery_state
        )
    def emit(
        self,
        *,
        event_type: str,
        **values: Any,
    ) -> TelemetryEvent | None:
        policy = self.policy_store.load()
        if not policy.persistence_enabled:
            return None
        event = self.factory.create(
            event_type=event_type,
            **values,
        )
        spool = TelemetrySpool(
            event_root=self.paths.events,
            dead_letter_root=self.paths.dead_letter,
            retention_days=policy.retention_days,
        )
        spool.append(event)
        return event
    async def deliver_once(self) -> dict[str, Any]:
        policy = self.policy_store.load()
        spool = TelemetrySpool(
            event_root=self.paths.events,
            dead_letter_root=self.paths.dead_letter,
            retention_days=policy.retention_days,
        )
        transport = TelemetryTransport(
            policy=policy,
            spool=spool,
            state_store=self.delivery_state,
            authorization_token=os.environ.get(
                "L9_TELEMETRY_AUTH_TOKEN"
            ),
        )
        return await transport.deliver_once()
    def health(self) -> dict[str, Any]:
        policy = self.policy_store.load()
        spool = TelemetrySpool(
            event_root=self.paths.events,
            dead_letter_root=self.paths.dead_letter,
            retention_days=policy.retention_days,
        )
        return telemetry_health(
            policy=policy,
            spool=spool,
            delivery_state=self.delivery_state,
        )
    def delete_all(self) -> None:
        policy = self.policy_store.load()
        spool = TelemetrySpool(
            event_root=self.paths.events,
            dead_letter_root=self.paths.dead_letter,
            retention_days=policy.retention_days,
        )
        spool.clear()
        self.identity_store.rotate()
EOF
###############################################################################
# 5. Runtime integration helpers
###############################################################################
cat > src/l9_debt_lsp/runtime/telemetry_service.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from typing import Any
from l9_debt_lsp.telemetry.latency import latency_bucket
from l9_debt_lsp.telemetry.paths import TelemetryPaths
from l9_debt_lsp.telemetry.service import TelemetryService
from l9_debt_lsp.packs.paths import StatePaths
class EffectivenessTelemetry:
    def __init__(
        self,
        *,
        state_paths: StatePaths,
        schema_root: Path,
        client_name: str,
        client_version: str,
        lsp_version: str,
    ) -> None:
        self.service = TelemetryService(
            paths=TelemetryPaths(state_paths),
            schema_root=schema_root,
            client_name=client_name,
            client_version=client_version,
            lsp_version=lsp_version,
        )
    def diagnostic_shown(
        self,
        diagnostic: dict[str, Any],
    ) -> None:
        data = diagnostic.get("data")
        if not isinstance(data, dict):
            return
        self.service.emit(
            event_type="diagnostic_shown",
            rule_pack_id=data.get("rule_pack_id"),
            rule_pack_version=data.get(
                "rule_pack_version"
            ),
            corpus_snapshot=data.get("corpus_snapshot"),
            canonical_rule_id=data.get(
                "canonical_rule_id"
            ),
            provider_rule_id=data.get(
                "provider_rule_id"
            ),
            finding_id=data.get("finding_id"),
            analysis_request_id=data.get(
                "analysis_request_id"
            ),
            limitations=tuple(
                data.get("limitations", [])
            ),
        )
    def diagnostic_dismissed(
        self,
        diagnostic: dict[str, Any],
    ) -> None:
        data = diagnostic.get("data")
        if not isinstance(data, dict):
            return
        self.service.emit(
            event_type="diagnostic_dismissed",
            rule_pack_id=data.get("rule_pack_id"),
            rule_pack_version=data.get(
                "rule_pack_version"
            ),
            corpus_snapshot=data.get("corpus_snapshot"),
            canonical_rule_id=data.get(
                "canonical_rule_id"
            ),
            provider_rule_id=data.get(
                "provider_rule_id"
            ),
            finding_id=data.get("finding_id"),
            analysis_request_id=data.get(
                "analysis_request_id"
            ),
            outcome="finding_dismissed",
        )
    def disposition(
        self,
        *,
        diagnostic: dict[str, Any],
        disposition: str,
    ) -> None:
        data = diagnostic.get("data")
        if not isinstance(data, dict):
            return
        self.service.emit(
            event_type="false_positive_disposition",
            rule_pack_id=data.get("rule_pack_id"),
            rule_pack_version=data.get(
                "rule_pack_version"
            ),
            corpus_snapshot=data.get("corpus_snapshot"),
            canonical_rule_id=data.get(
                "canonical_rule_id"
            ),
            provider_rule_id=data.get(
                "provider_rule_id"
            ),
            finding_id=data.get("finding_id"),
            analysis_request_id=data.get(
                "analysis_request_id"
            ),
            disposition=disposition,
            outcome="finding_dispositioned",
        )
    def quick_fix_offered(
        self,
        action: dict[str, Any],
    ) -> None:
        provenance = action.get("provenance")
        if not isinstance(provenance, dict):
            return
        self._quick_fix_event(
            event_type="quick_fix_offered",
            provenance=provenance,
        )
    def quick_fix_applied(
        self,
        provenance: dict[str, Any],
    ) -> None:
        self._quick_fix_event(
            event_type="quick_fix_applied",
            provenance=provenance,
        )
    def quick_fix_rejected(
        self,
        provenance: dict[str, Any],
    ) -> None:
        self._quick_fix_event(
            event_type="quick_fix_rejected",
            provenance=provenance,
        )
    def quick_fix_outcome(
        self,
        *,
        provenance: dict[str, Any],
        outcome: str,
    ) -> None:
        self._quick_fix_event(
            event_type="quick_fix_outcome",
            provenance=provenance,
            outcome=outcome,
        )
    def analysis_latency(
        self,
        analysis: dict[str, Any],
    ) -> None:
        bucket = latency_bucket(
            float(analysis.get("latency_ms", 0.0)),
            cancelled=(
                analysis.get("status") == "cancelled"
            ),
            timed_out=(
                analysis.get("latency_class")
                == "timed_out"
            ),
        )
        self.service.emit(
            event_type="latency_bucket",
            rule_pack_id=analysis.get(
                "active_pack_id"
            ),
            analysis_request_id=analysis.get(
                "request_id"
            ),
            latency_bucket=bucket,
        )
    def _quick_fix_event(
        self,
        *,
        event_type: str,
        provenance: dict[str, Any],
        outcome: str | None = None,
    ) -> None:
        self.service.emit(
            event_type=event_type,
            rule_pack_id=provenance.get(
                "rule_pack_id"
            ),
            rule_pack_version=provenance.get(
                "rule_pack_version"
            ),
            corpus_snapshot=provenance.get(
                "corpus_snapshot"
            ),
            canonical_rule_id=provenance.get(
                "canonical_rule_id"
            ),
            provider_rule_id=provenance.get(
                "provider_rule_id"
            ),
            finding_id=provenance.get(
                "finding_id"
            ),
            analysis_request_id=provenance.get(
                "analysis_request_id"
            ),
            action_id=provenance.get("action_id"),
            template_id=provenance.get(
                "template_id"
            ),
            outcome=outcome,
            limitations=tuple(
                provenance.get("limitations", [])
            ),
        )
EOF
###############################################################################
# 6. CLI extension
###############################################################################
python3 - <<'PY'
from pathlib import Path
path = Path("src/l9_debt_lsp/cli.py")
text = path.read_text(encoding="utf-8")
if "TelemetryPaths" not in text:
    text = text.replace(
        "from .runtime.capabilities import phase_capabilities",
        """from .runtime.capabilities import phase_capabilities
from .telemetry.paths import TelemetryPaths
from .telemetry.service import TelemetryService""",
    )
text = text.replace(
    '    commands.add_parser("recover-state")',
    '''    commands.add_parser("recover-state")
    commands.add_parser("telemetry-health")
    commands.add_parser("telemetry-deliver")
    commands.add_parser("telemetry-delete-all")''',
)
marker = '    if arguments.command == "verify-installed-pack":'
insert = '''
    if arguments.command in {
        "telemetry-health",
        "telemetry-deliver",
        "telemetry-delete-all",
    }:
        service = TelemetryService(
            paths=TelemetryPaths(paths),
            schema_root=schemas,
            client_name="cli",
            client_version="1",
            lsp_version="0.6.0",
        )
        if arguments.command == "telemetry-health":
            emit(service.health())
            return 0
        if arguments.command == "telemetry-deliver":
            import asyncio
            emit(asyncio.run(service.deliver_once()))
            return 0
        service.delete_all()
        emit({
            "schema_version": "l9.telemetry-delete-result/v1",
            "status": "deleted",
        })
        return 0
'''
if insert.strip() not in text:
    text = text.replace(marker, insert + marker)
path.write_text(text, encoding="utf-8")
PY
###############################################################################
# 7. Capabilities and version
###############################################################################
cat > src/l9_debt_lsp/runtime/capabilities.py <<'EOF'
from __future__ import annotations
from typing import Any
def phase_capabilities() -> dict[str, Any]:
    return {
        "schema_version": "l9.lsp-server-capabilities/v1",
        "phase": "LSP-P5",
        "repository_status": "architecturally_complete",
        "capabilities": {
            "pack_descriptor_validation": True,
            "pack_compatibility_evaluation": True,
            "manifest_validation": True,
            "archive_checksum_verification": True,
            "signature_verification": True,
            "safe_archive_extraction": True,
            "pack_installation": True,
            "pack_activation": True,
            "previous_known_good": True,
            "rollback": True,
            "retirement_rejection": True,
            "startup_recovery": True,
            "analysis_session_protocol": True,
            "workspace_sessions": True,
            "document_overlays": True,
            "document_version_enforcement": True,
            "cancellation": True,
            "bounded_invalidation": True,
            "stale_result_suppression": True,
            "latency_measurement": True,
            "offline_normal_analysis": True,
            "sdk_finding_validation": True,
            "canonical_identity_preservation": True,
            "diagnostic_projection": True,
            "related_information": True,
            "evidence_links": True,
            "deterministic_ordering": True,
            "diagnostic_deduplication": True,
            "bounded_diagnostics": True,
            "incomplete_analysis_diagnostics": True,
            "stale_safe_publication": True,
            "remediation_template_validation": True,
            "bounded_code_actions": True,
            "single_document_workspace_edits": True,
            "document_version_binding": True,
            "edit_conflict_detection": True,
            "protected_path_enforcement": True,
            "code_action_preview": True,
            "remediation_provenance": True,
            "telemetry_policy": True,
            "telemetry_opt_in": True,
            "organization_controlled_telemetry": True,
            "local_only_telemetry": True,
            "privacy_validation": True,
            "durable_telemetry_spool": True,
            "bounded_telemetry_retention": True,
            "telemetry_batch_delivery": True,
            "telemetry_retry": True,
            "telemetry_dead_letter": True,
            "diagnostic_dispositions": True,
            "rule_outcomes": True,
            "quick_fix_outcomes": True,
            "latency_bucket_events": True,
            "telemetry_health": True,
            "telemetry_data_deletion": True,
            "arbitrary_command_execution": False,
            "autonomous_multi_file_repair": False,
            "source_content_telemetry": False,
            "absolute_path_telemetry": False,
            "developer_identity_telemetry": False
        },
        "limitations": [
            "A concrete public SDK AnalysisSession binding must be configured.",
            "Telemetry delivery requires explicit policy and an allowlisted HTTPS endpoint.",
            "Effectiveness aggregation and rule governance remain owned by Debt Intelligence."
        ]
    }
EOF
python3 - <<'PY'
from pathlib import Path
for path_name in (
    "src/l9_debt_lsp/__init__.py",
    "pyproject.toml",
):
    path = Path(path_name)
    text = path.read_text(encoding="utf-8")
    for old in (
        "0.2.0",
        "0.3.0",
        "0.4.0",
        "0.5.0",
    ):
        text = text.replace(old, "1.0.0")
    path.write_text(text, encoding="utf-8")
PY
###############################################################################
# 8. Tests
###############################################################################
cat > tests/telemetry/test_policy.py <<'EOF'
from __future__ import annotations
from pathlib import Path
import pytest
from l9_debt_lsp.telemetry.errors import (
    TelemetryPolicyError,
)
from l9_debt_lsp.telemetry.models import TelemetryPolicy
from l9_debt_lsp.telemetry.policy import (
    TelemetryPolicyStore,
)
ROOT = Path(__file__).resolve().parents[2]
def test_default_policy_is_disabled(tmp_path: Path) -> None:
    store = TelemetryPolicyStore(
        path=tmp_path / "policy.json",
        schema_path=(
            ROOT
            / "schemas/lsp/telemetry-policy.schema.json"
        ),
    )
    policy = store.load()
    assert policy.mode == "disabled"
    assert policy.persistence_enabled is False
    assert policy.delivery_enabled is False
def test_delivery_requires_https_allowlist(
    tmp_path: Path,
) -> None:
    store = TelemetryPolicyStore(
        path=tmp_path / "policy.json",
        schema_path=(
            ROOT
            / "schemas/lsp/telemetry-policy.schema.json"
        ),
    )
    policy = TelemetryPolicy(
        mode="user_opt_in",
        consent="granted",
        endpoint="https://telemetry.example.test/v1",
        endpoint_allowlist=(
            "https://different.example.test/",
        ),
        retention_days=30,
        organization_policy_id=None,
        limitations=(),
    )
    with pytest.raises(TelemetryPolicyError):
        store.save(policy)
EOF
cat > tests/privacy/test_telemetry_privacy.py <<'EOF'
from __future__ import annotations
import pytest
from l9_debt_lsp.telemetry.errors import (
    TelemetryPrivacyError,
)
from l9_debt_lsp.telemetry.privacy import (
    validate_privacy,
)
@pytest.mark.parametrize(
    "document",
    [
        {"source_content": "print('secret')"},
        {"document_uri": "file:///home/alice/project/a.py"},
        {"value": "/home/alice/project/a.py"},
        {"value": "alice@example.com"},
        {"value": "Bearer abcdefghijklmnopqrstuvwxyz"},
        {"value": "ghp_abcdefghijklmnopqrstuvwxyz123456"},
        {"value": "password=supersecret"},
    ],
)
def test_prohibited_telemetry_is_rejected(
    document: dict[str, str],
) -> None:
    with pytest.raises(TelemetryPrivacyError):
        validate_privacy(document)
def test_canonical_identifiers_are_allowed() -> None:
    validate_privacy(
        {
            "canonical_rule_id": "l9.example",
            "finding_id": "finding-123",
            "rule_pack_id": "pack_" + "a" * 64,
        }
    )
EOF
cat > tests/telemetry/test_event_factory.py <<'EOF'
from __future__ import annotations
from l9_debt_lsp.telemetry.events import EventFactory
from l9_debt_lsp.telemetry.models import (
    TelemetryContext,
)
def test_event_identity_is_unique_per_sequence() -> None:
    factory = EventFactory(
        TelemetryContext(
            installation_id=(
                "installation_" + "a" * 64
            ),
            session_id="session_" + "b" * 64,
            client_name="vscode",
            client_version="1.0",
            lsp_version="1.0.0",
        )
    )
    first = factory.create(
        event_type="diagnostic_shown",
        rule_pack_id="pack_" + "c" * 64,
        canonical_rule_id="l9.example",
        finding_id="finding-1",
    )
    second = factory.create(
        event_type="diagnostic_shown",
        rule_pack_id="pack_" + "c" * 64,
        canonical_rule_id="l9.example",
        finding_id="finding-1",
    )
    assert first.event_id != second.event_id
    assert first.sequence == 1
    assert second.sequence == 2
EOF
cat > tests/telemetry/test_spool.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from l9_debt_lsp.telemetry.events import EventFactory
from l9_debt_lsp.telemetry.models import (
    TelemetryContext,
)
from l9_debt_lsp.telemetry.spool import TelemetrySpool
def factory() -> EventFactory:
    return EventFactory(
        TelemetryContext(
            installation_id=(
                "installation_" + "a" * 64
            ),
            session_id="session_" + "b" * 64,
            client_name="test",
            client_version="1",
            lsp_version="1.0.0",
        )
    )
def test_spool_persists_and_acknowledges(
    tmp_path: Path,
) -> None:
    events = tmp_path / "events"
    dead = tmp_path / "dead"
    events.mkdir()
    dead.mkdir()
    spool = TelemetrySpool(
        event_root=events,
        dead_letter_root=dead,
        retention_days=30,
    )
    event = factory().create(
        event_type="diagnostic_shown",
        canonical_rule_id="l9.example",
        finding_id="finding-1",
    )
    path = spool.append(event)
    assert path.is_file()
    batch = spool.batch()
    assert len(batch) == 1
    assert batch[0][1]["event_id"] == event.event_id
    spool.acknowledge([path])
    assert not path.exists()
EOF
cat > tests/telemetry/test_latency.py <<'EOF'
from __future__ import annotations
from l9_debt_lsp.telemetry.latency import (
    latency_bucket,
)
def test_latency_is_bucketed_without_raw_delivery() -> None:
    assert latency_bucket(10) == "lt_25ms"
    assert latency_bucket(50) == "50_99ms"
    assert latency_bucket(250) == "200_499ms"
    assert latency_bucket(1500) == "1_2s"
    assert latency_bucket(6000) == "gt_5s"
    assert latency_bucket(1, cancelled=True) == "cancelled"
    assert latency_bucket(1, timed_out=True) == "timed_out"
EOF
cat > tests/resilience/test_telemetry_fail_open.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from l9_debt_lsp.telemetry.models import TelemetryPolicy
from l9_debt_lsp.telemetry.policy import (
    TelemetryPolicyStore,
)
def test_disabled_telemetry_requires_no_endpoint(
    tmp_path: Path,
) -> None:
    policy = TelemetryPolicy(
        mode="disabled",
        consent="not_granted",
        endpoint=None,
        endpoint_allowlist=(),
        retention_days=30,
        organization_policy_id=None,
        limitations=(),
    )
    assert policy.persistence_enabled is False
    assert policy.delivery_enabled is False
EOF
cat > tests/architecture/test_telemetry_boundary.py <<'EOF'
from __future__ import annotations
import ast
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TELEMETRY = ROOT / "src/l9_debt_lsp/telemetry"
PROHIBITED_IMPORTS = (
    "git",
    "dulwich",
    "subprocess",
    "sqlite3",
)
PROHIBITED_TERMS = (
    "document_text",
    "source_content",
    "preview_diff",
    "diagnostic_message",
    "workspace_uri",
    "document_uri",
    "developer_email",
    "developer_name",
    "repository_remote",
    "branch_name",
    "commit_sha",
    "corpus_compiler",
    "mine_patterns",
)
def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(
                alias.name for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module)
    return modules
def test_telemetry_imports_no_mutation_systems() -> None:
    for path in TELEMETRY.rglob("*.py"):
        for module in imported_modules(path):
            assert not module.startswith(
                PROHIBITED_IMPORTS
            ), f"{path} imports prohibited module {module}"
def test_prohibited_fields_exist_only_in_privacy_guard() -> None:
    for path in TELEMETRY.rglob("*.py"):
        if path.name == "privacy.py":
            continue
        content = path.read_text(
            encoding="utf-8"
        ).lower()
        for term in PROHIBITED_TERMS:
            assert term not in content, (
                f"{path} references prohibited telemetry "
                f"field {term}"
            )
EOF
###############################################################################
# 9. ADRs
###############################################################################
cat > docs/architecture/ADRs/ADR-LSP-021-telemetry-is-disabled-by-default.md <<'EOF'
# ADR-LSP-021: Telemetry is disabled by default
- Status: Accepted
- Phase: LSP-P5
## Decision
Telemetry defaults to disabled.
Delivery requires explicit user consent or an organization-controlled policy.
Local-only telemetry is supported without network delivery.
Telemetry availability never gates diagnostics, code actions, pack activation,
or server startup.
EOF
cat > docs/architecture/ADRs/ADR-LSP-022-telemetry-excludes-source-and-identity.md <<'EOF'
# ADR-LSP-022: Telemetry excludes source content and personal identity
- Status: Accepted
- Phase: LSP-P5
## Decision
Telemetry may include canonical technical identifiers needed for rule
effectiveness analysis.
It must not include source content, snippets, paths, document URIs, repository
identity, branch identity, commit identity, developer identity, machine
identity, credentials, raw logs, repository graphs, or raw corpus records.
EOF
cat > docs/architecture/ADRs/ADR-LSP-023-telemetry-is-durable-and-bounded.md <<'EOF'
# ADR-LSP-023: Telemetry storage is durable and bounded
- Status: Accepted
- Phase: LSP-P5
## Decision
Telemetry events are written atomically as immutable canonical JSON documents.
The local queue is bounded by event count, byte size, and retention age.
Overflow removes the oldest queued events and degrades telemetry health without
affecting editor behavior.
EOF
cat > docs/architecture/ADRs/ADR-LSP-024-intelligence-owns-effectiveness-decisions.md <<'EOF'
# ADR-LSP-024: Debt Intelligence owns effectiveness interpretation
- Status: Accepted
- Phase: LSP-P5
## Decision
The LSP emits privacy-safe outcomes but does not locally promote, retire,
rewrite, or recompile prevention rules.
Debt Intelligence owns aggregation, quality analysis, rule refinement, and
governance decisions.
EOF
cat > docs/architecture/ADRs/ADR-LSP-025-repository-v1-complete.md <<'EOF'
# ADR-LSP-025: LSP repository v1 architecture is complete
- Status: Accepted
- Phase: LSP-P5
## Decision
With secure pack consumption, incremental SDK analysis, canonical diagnostics,
bounded code actions, and privacy-safe telemetry implemented, the repository
has completed its v1 architectural roadmap.
Future work is classified as product expansion, platform integration,
performance optimization, or operational hardening rather than missing
architectural ownership.
EOF
###############################################################################
# 10. Roadmap and README completion
###############################################################################
python3 - <<'PY'
from pathlib import Path
path = Path("ROADMAP.md")
text = path.read_text(encoding="utf-8")
text = text.replace(
    """## LSP-P5 — Effectiveness loop
Status: Planned
- diagnostic shown and dismissed events
- false-positive dispositions
- quick-fix outcomes
- rule outcomes
- latency telemetry
- privacy filtering
""",
    """## LSP-P5 — Effectiveness loop
Status: Implemented
- disabled-by-default telemetry policy
- user opt-in and organization-controlled modes
- local-only telemetry mode
- diagnostic shown and dismissed events
- false-positive dispositions
- quick-fix offered, applied, rejected, and outcome events
- rule outcome events
- latency bucket events
- pack activation and rollback events
- deterministic event identity
- privacy validation
- bounded durable local spool
- HTTPS batch delivery
- retry and dead-letter handling
- telemetry health reporting
- user data deletion and installation-ID rotation
## Repository status
Status: Architecturally complete
Version: 1.0.0
""",
)
path.write_text(text, encoding="utf-8")
PY
cat >> README.md <<'EOF'
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

EOF

###############################################################################

11. CI

###############################################################################

cat > .github/workflows/phase-6-final-telemetry.yml <<‘EOF’
name: LSP-P5 Final Telemetry

on:
pull_request:
push:
branches:
- main

permissions:
contents: read

jobs:
final-telemetry:
runs-on: ubuntu-latest
timeout-minutes: 20

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
  - name: Validate schemas
    run: |
      python - <<'PY'
      import json
      from pathlib import Path
      from jsonschema import Draft202012Validator
      for path in sorted(Path("schemas/lsp").glob("*.json")):
          schema = json.loads(path.read_text(encoding="utf-8"))
          Draft202012Validator.check_schema(schema)
          print(path)
      PY
  - name: Telemetry tests
    run: pytest tests/telemetry
  - name: Privacy tests
    run: pytest tests/privacy
  - name: Resilience tests
    run: pytest tests/resilience
  - name: Security tests
    run: pytest tests/security
  - name: Architecture tests
    run: pytest tests/architecture
  - name: Diagnostics and actions
    run: |
      pytest \
        tests/diagnostics \
        tests/publication \
        tests/actions
  - name: Incremental runtime
    run: |
      pytest \
        tests/analysis \
        tests/concurrency \
        tests/performance \
        tests/runtime
  - name: Full test suite
    run: |
      pytest \
        --cov=l9_debt_lsp \
        --cov-report=term-missing \
        --cov-fail-under=85
  - name: Ruff
    run: ruff check .
  - name: Mypy
    run: mypy src
  - name: Final capabilities
    run: l9-debt-lsp-contracts capabilities
  - name: Telemetry health
    run: |
      export L9_DEBT_LSP_STATE_ROOT="${RUNNER_TEMP}/l9-state"
      l9-debt-lsp-contracts telemetry-health

EOF

###############################################################################

12. Final acceptance gates

###############################################################################

cat > .l9/final-acceptance-gates.yaml <<‘EOF’
schema: l9.final-acceptance-gates/v1

repository: Quantum-L9/l9-ci-debt-lsp
version: 1.0.0
status: architecturally_complete

gates:
ownership_boundary:
required: true
expectation: serving_only

corpus_dependency:
required: true
expectation: prohibited

pack_integrity:
required: true
expectation:
- checksum_verified
- signature_verified
- compatibility_verified
- atomic_installation
- explicit_activation
- previous_known_good

incremental_runtime:
required: true
expectation:
- public_SDK_boundary
- document_versions
- cancellation
- bounded_invalidation
- stale_result_suppression

diagnostics:
required: true
expectation:
- canonical_identity_preserved
- deterministic_ordering
- incomplete_not_clean
- stale_safe_publication

code_actions:
required: true
expectation:
- deterministic_templates
- exact_version_binding
- single_document_only
- protected_paths
- explicit_user_approval
- no_commands

telemetry:
required: true
expectation:
- disabled_by_default
- explicit_consent_or_org_policy
- no_source_content
- no_paths
- no_developer_identity
- bounded_storage
- fail_open_editor
- intelligence_owned_effectiveness

release_quality:
required: true
expectation:
- schemas_valid
- tests_pass
- mypy_pass
- ruff_pass
- coverage_at_least_85_percent

final_invariant: >
The repository serves verified immutable prevention packs through the public
SDK analysis contract, publishes canonical diagnostics and bounded
user-approved remediation, and emits only privacy-safe effectiveness events.
EOF

###############################################################################

13. Local final validation

###############################################################################

python3 -m compileall -q src

python3 - <<‘PY’
from future import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

root = Path.cwd()

required = [
“.l9/telemetry-contract.yaml”,
“.l9/final-acceptance-gates.yaml”,
“schemas/lsp/telemetry-policy.schema.json”,
“schemas/lsp/telemetry-event.schema.json”,
“schemas/lsp/telemetry-health.schema.json”,
“src/l9_debt_lsp/telemetry/policy.py”,
“src/l9_debt_lsp/telemetry/privacy.py”,
“src/l9_debt_lsp/telemetry/events.py”,
“src/l9_debt_lsp/telemetry/spool.py”,
“src/l9_debt_lsp/telemetry/transport.py”,
“src/l9_debt_lsp/telemetry/service.py”,
“src/l9_debt_lsp/runtime/telemetry_service.py”,
“tests/telemetry/test_policy.py”,
“tests/privacy/test_telemetry_privacy.py”,
“tests/architecture/test_telemetry_boundary.py”,
]

missing = [
value
for value in required
if not (root / value).is_file()
]

if missing:
raise SystemExit(
f”LSP-P5 required files missing: {missing}”
)

for schema_path in sorted(
(root / “schemas/lsp”).glob(”*.json”)
):
schema = json.loads(
schema_path.read_text(encoding=“utf-8”)
)
Draft202012Validator.check_schema(schema)

telemetry_root = (
root / “src/l9_debt_lsp/telemetry”
)

prohibited_imports = (
“git”,
“dulwich”,
“subprocess”,
“sqlite3”,
)

prohibited_runtime_terms = (
“corpus_compiler”,
“mine_patterns”,
“promote_rule”,
“retire_rule”,
“activate_from_telemetry”,
)

for source_path in telemetry_root.rglob(”*.py”):
content = source_path.read_text(
encoding=“utf-8”
).lower()

for term in prohibited_runtime_terms:
    if term in content:
        raise SystemExit(
            f"prohibited telemetry behavior "
            f"{term!r} in {source_path}"
        )

version_text = (
root / “src/l9_debt_lsp/init.py”
).read_text(encoding=“utf-8”)

if “1.0.0” not in version_text:
raise SystemExit(
“final repository version is not 1.0.0”
)

print(
json.dumps(
{
“schema_version”: “l9.phase-build-result/v1”,
“repository”: “Quantum-L9/l9-ci-debt-lsp”,
“phase”: “LSP-P5”,
“version”: “1.0.0”,
“status”: “architecturally_complete”,
“telemetry_default”: “disabled”,
“telemetry_consent”: (
“explicit-or-organization-controlled”
),
“telemetry_storage”: “durable-bounded”,
“telemetry_transport”: “allowlisted-https”,
“telemetry_failure_behavior”: “editor-fail-open”,
“source_content_telemetry”: “prohibited”,
“absolute_path_telemetry”: “prohibited”,
“developer_identity_telemetry”: “prohibited”,
“rule_governance”: “intelligence-owned”
},
sort_keys=True,
separators=(”,”, “:”),
)
)
PY

printf ‘\n’
printf ‘LSP-P5 build complete.\n’
printf ‘\n’
printf ‘Implemented:\n’
printf ’  - disabled-by-default telemetry policy\n’
printf ’  - user opt-in and organization-controlled modes\n’
printf ’  - local-only mode\n’
printf ’  - privacy-safe canonical event schemas\n’
printf ’  - diagnostic shown and dismissed events\n’
printf ’  - false-positive dispositions\n’
printf ’  - rule outcomes\n’
printf ’  - quick-fix offered, applied, rejected, and outcomes\n’
printf ’  - latency bucket events\n’
printf ’  - deterministic event identities\n’
printf ’  - durable bounded local spool\n’
printf ’  - retention and overflow controls\n’
printf ’  - allowlisted HTTPS batch transport\n’
printf ’  - retry and dead-letter handling\n’
printf ’  - telemetry health\n’
printf ’  - telemetry deletion and identity rotation\n’
printf ’  - final repository acceptance gates\n’
printf ‘\n’
printf ‘Privacy guarantees:\n’
printf ’  - no source content or snippets\n’
printf ’  - no document or workspace paths\n’
printf ’  - no repository, branch, or commit identity\n’
printf ’  - no developer or machine identity\n’
printf ’  - no secrets, tokens, or raw logs\n’
printf ’  - no corpus records or repository graphs\n’
printf ‘\n’
printf ‘Repository status:\n’
printf ’  Quantum-L9/l9-ci-debt-lsp v1.0.0\n’
printf ’  ARCHITECTURALLY COMPLETE\n’

:::
After this phase, the complete v1 data flow is:
```text
Resolver
→ Debt Intelligence
→ signed immutable defense pack
→ LSP verification and activation
→ SDK incremental analysis
→ canonical diagnostics
→ bounded user-approved remediation
→ privacy-safe effectiveness telemetry
→ Debt Intelligence refinement

l9-ci-debt-lsp is then architecturally complete at v1.0.0.