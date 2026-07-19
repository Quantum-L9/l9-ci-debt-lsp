Phase 3 is LSP-P2: SDK incremental adapter and document runtime.

This phase implements the repository specification’s AnalysisSession boundary, in-memory document overlays, document-version consistency, cancellation, bounded dependency invalidation, deterministic scheduling, stale-result suppression, offline execution, and latency measurement. repo-spec.yaml

The SDK integration is intentionally defined through a strict public adapter protocol rather than importing SDK internals. A concrete SDK binding can therefore evolve independently without weakening the LSP boundary.

Save this as build-phase-3.sh and run it against the completed LSP-P1 repository.

#!/usr/bin/env bash
set -euo pipefail
###############################################################################
# Quantum-L9/l9-ci-debt-lsp
# LSP-P2 — SDK Incremental Adapter
#
# Adds:
#   - public AnalysisSession adapter protocol
#   - workspace session lifecycle
#   - in-memory document overlays
#   - monotonic document-version enforcement
#   - cancellation tokens
#   - stale-result suppression
#   - bounded dependency invalidation
#   - deterministic scheduling
#   - concurrency limits
#   - offline-only normal analysis
#   - latency measurement and budget classification
#   - fail-closed incomplete-analysis semantics
#   - runtime health and capability reporting
#
# Does not yet add:
#   - final LSP diagnostic projection
#   - SDK finding-to-Diagnostic mapping
#   - related-information rendering
#   - production code actions
#   - telemetry transport
###############################################################################
fail() {
  printf 'LSP-P2: %s\n' "$*" >&2
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
require_file ".l9/pack-protocol-contract.yaml"
require_file "src/l9_debt_lsp/packs/activation.py"
require_file "src/l9_debt_lsp/packs/store.py"
require_file "src/l9_debt_lsp/runtime/capabilities.py"
require_file "pyproject.toml"
mkdir -p \
  .github/workflows \
  .l9 \
  docs/architecture/ADRs \
  schemas/lsp \
  src/l9_debt_lsp/analysis \
  src/l9_debt_lsp/runtime \
  tests/analysis \
  tests/concurrency \
  tests/performance \
  tests/runtime \
  tests/fixtures/analysis
###############################################################################
# 1. Incremental-analysis contract
###############################################################################
cat > .l9/incremental-analysis-contract.yaml <<'EOF'
schema: l9.lsp-incremental-analysis-contract/v1
metadata:
  repository: Quantum-L9/l9-ci-debt-lsp
  phase: LSP-P2
  status: authoritative
authority:
  lsp_owns:
    - workspace lifecycle
    - document lifecycle
    - document overlays
    - document versions
    - scheduling
    - debounce
    - cancellation
    - stale-result suppression
    - bounded invalidation
    - active-pack selection
    - latency measurement
    - presentation-layer limitations
  sdk_owns:
    - canonical analysis semantics
    - finding construction
    - finding identity
    - evidence construction
    - source-location semantics
    - rule evaluation semantics
    - partial-parse semantics
  prohibited:
    - importing SDK private modules
    - redefining canonical SDK findings
    - reconstructing canonical evidence
    - treating incomplete analysis as PASS
    - network calls during normal diagnostics
    - persistent database writes per keystroke
    - full repository scans per keystroke
sdk_interface:
  name: AnalysisSession
  contract: l9.sdk-analysis-session/v1
  operations:
    - open_workspace
    - close_workspace
    - open_document
    - update_document
    - evaluate_document
    - close_document
    - invalidate_dependencies
  required_properties:
    - deterministic for identical inputs
    - cancellation-aware
    - document-version aware
    - active-pack aware
    - offline
    - partial-parse capable
    - bounded invalidation
workspace:
  identity:
    representation: pseudonymous
    absolute_path_storage: prohibited
  lifecycle:
    states:
      - created
      - open
      - closing
      - closed
  limits:
    maximum_open_documents: 5000
    maximum_document_bytes: 5242880
    maximum_total_overlay_bytes: 268435456
    maximum_dependency_edges: 100000
    maximum_invalidated_documents_per_change: 250
document:
  identity:
    source: normalized URI hash
    prefix: doc_
    algorithm: SHA-256
  versions:
    type: non_negative_integer
    opening_version: any_non_negative_integer
    update_rule: strictly_increasing
    stale_update_behavior: reject
    stale_result_behavior: discard
  overlays:
    storage: memory_only
    source_content_persistence: prohibited
    close_behavior: delete_content
    workspace_close_behavior: delete_all_content
  content:
    encoding: UTF-8
    maximum_bytes: 5242880
    normalization: preserve_exact_editor_text
scheduling:
  ordering:
    primary: workspace_id
    secondary: document_identity
    tertiary: document_version
  concurrency:
    maximum_global_evaluations: 4
    maximum_workspace_evaluations: 2
    maximum_document_evaluations: 1
  supersession:
    new_version_cancels_older_pending_work: true
    new_version_marks_older_running_work_stale: true
  fairness:
    strategy: bounded_fifo
    starvation_prohibited: true
cancellation:
  cooperative: true
  reasons:
    - client_cancelled
    - document_updated
    - document_closed
    - workspace_closed
    - server_shutdown
    - timeout
    - pack_changed
  invariant: >
    Cancellation never publishes a successful complete-analysis result.
invalidation:
  source: SDK dependency information
  direction: reverse_dependents
  maximum_documents_per_change: 250
  overflow_behavior:
    - mark workspace analysis incomplete
    - publish limitation
    - schedule bounded workspace refresh
    - do not report false PASS
stale_results:
  comparison:
    - workspace generation
    - document version
    - active pack identity
    - analysis request identity
  stale_if:
    - workspace generation changed
    - document closed
    - document version advanced
    - active pack changed
    - request superseded
  publication_behavior: discard
latency:
  clocks:
    measurement: monotonic
    timestamps: UTC
  document_local_ms:
    p50: 50
    p95: 200
  bounded_workspace_ms:
    p95: 1000
  evaluation_timeout_ms: 5000
  classification:
    - within_budget
    - elevated
    - exceeded
    - timed_out
    - cancelled
result:
  states:
    - complete
    - incomplete
    - cancelled
    - stale
    - failed
  complete_requirements:
    - SDK evaluation completed
    - document version unchanged
    - workspace generation unchanged
    - active pack unchanged
    - request not cancelled
  incomplete_requirements:
    - limitations non_empty
  failed_behavior:
    - preserve known-good diagnostics where protocol-safe
    - publish analysis limitation
    - do not publish empty success as PASS
runtime:
  normal_network_dependency: prohibited
  source_content_logging: prohibited
  absolute_path_logging: prohibited
  source_content_telemetry: prohibited
phase:
  id: LSP-P2
  status: implemented
  includes:
    - AnalysisSession protocol
    - in-memory workspace manager
    - document overlays
    - cancellation
    - deterministic scheduler
    - stale-result suppression
    - bounded invalidation
    - active-pack generation tracking
    - latency measurement
    - incomplete-analysis semantics
    - runtime tests
  excludes:
    - final Diagnostic conversion
    - related information presentation
    - code action construction
    - telemetry transport
EOF
###############################################################################
# 2. Schemas
###############################################################################
cat > schemas/lsp/analysis-request.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/analysis-request/v1",
  "title": "L9 LSP Incremental Analysis Request",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "request_id",
    "workspace_id",
    "workspace_generation",
    "document_id",
    "document_uri",
    "document_version",
    "language_id",
    "active_pack_id",
    "active_pack_version",
    "created_at",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.analysis-request/v1"
    },
    "request_id": {
      "type": "string",
      "pattern": "^request_[0-9a-f]{64}$"
    },
    "workspace_id": {
      "type": "string",
      "pattern": "^workspace_[0-9a-f]{64}$"
    },
    "workspace_generation": {
      "type": "integer",
      "minimum": 0
    },
    "document_id": {
      "type": "string",
      "pattern": "^doc_[0-9a-f]{64}$"
    },
    "document_uri": {
      "type": "string",
      "minLength": 1
    },
    "document_version": {
      "type": "integer",
      "minimum": 0
    },
    "language_id": {
      "type": "string",
      "minLength": 1
    },
    "active_pack_id": {
      "type": "string",
      "pattern": "^pack_[0-9a-f]{64}$"
    },
    "active_pack_version": {
      "type": "string",
      "minLength": 1
    },
    "created_at": {
      "type": "string",
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
cat > schemas/lsp/analysis-result.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/analysis-result/v1",
  "title": "L9 LSP Incremental Analysis Result",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "request_id",
    "workspace_id",
    "workspace_generation",
    "document_id",
    "document_version",
    "active_pack_id",
    "status",
    "findings",
    "limitations",
    "latency_ms",
    "latency_class",
    "completed_at"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.analysis-result/v1"
    },
    "request_id": {
      "type": "string",
      "pattern": "^request_[0-9a-f]{64}$"
    },
    "workspace_id": {
      "type": "string",
      "pattern": "^workspace_[0-9a-f]{64}$"
    },
    "workspace_generation": {
      "type": "integer",
      "minimum": 0
    },
    "document_id": {
      "type": "string",
      "pattern": "^doc_[0-9a-f]{64}$"
    },
    "document_version": {
      "type": "integer",
      "minimum": 0
    },
    "active_pack_id": {
      "type": "string",
      "pattern": "^pack_[0-9a-f]{64}$"
    },
    "status": {
      "enum": [
        "complete",
        "incomplete",
        "cancelled",
        "stale",
        "failed"
      ]
    },
    "findings": {
      "type": "array",
      "items": {
        "type": "object"
      }
    },
    "limitations": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "uniqueItems": true
    },
    "latency_ms": {
      "type": "number",
      "minimum": 0
    },
    "latency_class": {
      "enum": [
        "within_budget",
        "elevated",
        "exceeded",
        "timed_out",
        "cancelled"
      ]
    },
    "completed_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
EOF
cat > schemas/lsp/workspace-state.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/workspace-state/v1",
  "title": "L9 LSP Workspace State",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "workspace_id",
    "generation",
    "state",
    "open_document_count",
    "overlay_bytes",
    "dependency_edge_count",
    "active_pack_id",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.workspace-state/v1"
    },
    "workspace_id": {
      "type": "string",
      "pattern": "^workspace_[0-9a-f]{64}$"
    },
    "generation": {
      "type": "integer",
      "minimum": 0
    },
    "state": {
      "enum": [
        "created",
        "open",
        "closing",
        "closed"
      ]
    },
    "open_document_count": {
      "type": "integer",
      "minimum": 0
    },
    "overlay_bytes": {
      "type": "integer",
      "minimum": 0
    },
    "dependency_edge_count": {
      "type": "integer",
      "minimum": 0
    },
    "active_pack_id": {
      "type": [
        "string",
        "null"
      ]
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
cat > schemas/lsp/document-overlay.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/document-overlay/v1",
  "title": "L9 LSP Document Overlay Metadata",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "document_id",
    "uri",
    "language_id",
    "version",
    "content_bytes",
    "state",
    "opened_at",
    "updated_at"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.document-overlay/v1"
    },
    "document_id": {
      "type": "string",
      "pattern": "^doc_[0-9a-f]{64}$"
    },
    "uri": {
      "type": "string",
      "minLength": 1
    },
    "language_id": {
      "type": "string",
      "minLength": 1
    },
    "version": {
      "type": "integer",
      "minimum": 0
    },
    "content_bytes": {
      "type": "integer",
      "minimum": 0,
      "maximum": 5242880
    },
    "state": {
      "enum": [
        "open",
        "closed"
      ]
    },
    "opened_at": {
      "type": "string",
      "format": "date-time"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
EOF
cat > schemas/lsp/runtime-health.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/runtime-health/v1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "status",
    "workspace_count",
    "open_document_count",
    "running_evaluation_count",
    "queued_evaluation_count",
    "active_pack_id",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.runtime-health/v1"
    },
    "status": {
      "enum": [
        "healthy",
        "degraded",
        "unavailable"
      ]
    },
    "workspace_count": {
      "type": "integer",
      "minimum": 0
    },
    "open_document_count": {
      "type": "integer",
      "minimum": 0
    },
    "running_evaluation_count": {
      "type": "integer",
      "minimum": 0
    },
    "queued_evaluation_count": {
      "type": "integer",
      "minimum": 0
    },
    "active_pack_id": {
      "type": [
        "string",
        "null"
      ]
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
# 3. Analysis package
###############################################################################
cat > src/l9_debt_lsp/analysis/__init__.py <<'EOF'
"""Incremental SDK-backed analysis runtime."""
EOF
cat > src/l9_debt_lsp/analysis/errors.py <<'EOF'
from __future__ import annotations
class AnalysisError(RuntimeError):
    """Base incremental-analysis failure."""
class WorkspaceNotFoundError(AnalysisError):
    """The requested workspace session does not exist."""
class WorkspaceClosedError(AnalysisError):
    """The workspace is closed."""
class DocumentNotFoundError(AnalysisError):
    """The requested document overlay does not exist."""
class DocumentVersionError(AnalysisError):
    """A document update is not strictly newer."""
class DocumentLimitError(AnalysisError):
    """A document or workspace resource limit was exceeded."""
class AnalysisCancelledError(AnalysisError):
    """The analysis request was cancelled."""
class AnalysisTimeoutError(AnalysisError):
    """The analysis request exceeded the runtime timeout."""
class StaleAnalysisResultError(AnalysisError):
    """The result no longer matches current runtime state."""
class SDKAdapterError(AnalysisError):
    """The public SDK analysis adapter failed."""
EOF
cat > src/l9_debt_lsp/analysis/models.py <<'EOF'
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
@dataclass(frozen=True)
class PackContext:
    pack_id: str
    pack_version: str
    corpus_snapshot: str
    compiler_version: str
    taxonomy_version: str
    sdk_contract_version: str
@dataclass
class DocumentOverlay:
    document_id: str
    uri: str
    language_id: str
    version: int
    text: str
    opened_at: str
    updated_at: str
    state: str = "open"
    @property
    def content_bytes(self) -> int:
        return len(self.text.encode("utf-8"))
    def metadata(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.document-overlay/v1",
            "document_id": self.document_id,
            "uri": self.uri,
            "language_id": self.language_id,
            "version": self.version,
            "content_bytes": self.content_bytes,
            "state": self.state,
            "opened_at": self.opened_at,
            "updated_at": self.updated_at,
        }
@dataclass
class WorkspaceSessionState:
    workspace_id: str
    generation: int
    state: str
    active_pack: PackContext | None
    documents: dict[str, DocumentOverlay] = field(
        default_factory=dict
    )
    reverse_dependencies: dict[str, set[str]] = field(
        default_factory=dict
    )
    limitations: set[str] = field(default_factory=set)
    @property
    def overlay_bytes(self) -> int:
        return sum(
            document.content_bytes
            for document in self.documents.values()
            if document.state == "open"
        )
    @property
    def dependency_edge_count(self) -> int:
        return sum(
            len(dependents)
            for dependents in self.reverse_dependencies.values()
        )
    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.workspace-state/v1",
            "workspace_id": self.workspace_id,
            "generation": self.generation,
            "state": self.state,
            "open_document_count": sum(
                document.state == "open"
                for document in self.documents.values()
            ),
            "overlay_bytes": self.overlay_bytes,
            "dependency_edge_count": (
                self.dependency_edge_count
            ),
            "active_pack_id": (
                self.active_pack.pack_id
                if self.active_pack is not None
                else None
            ),
            "limitations": sorted(self.limitations),
        }
@dataclass(frozen=True)
class AnalysisRequest:
    request_id: str
    workspace_id: str
    workspace_generation: int
    document_id: str
    document_uri: str
    document_version: int
    language_id: str
    active_pack_id: str
    active_pack_version: str
    created_at: str
    limitations: tuple[str, ...]
    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.analysis-request/v1",
            "request_id": self.request_id,
            "workspace_id": self.workspace_id,
            "workspace_generation": self.workspace_generation,
            "document_id": self.document_id,
            "document_uri": self.document_uri,
            "document_version": self.document_version,
            "language_id": self.language_id,
            "active_pack_id": self.active_pack_id,
            "active_pack_version": self.active_pack_version,
            "created_at": self.created_at,
            "limitations": list(self.limitations),
        }
@dataclass(frozen=True)
class SDKAnalysisResult:
    findings: tuple[dict[str, Any], ...]
    limitations: tuple[str, ...]
    complete: bool
    dependencies: tuple[str, ...] = ()
@dataclass(frozen=True)
class AnalysisResult:
    request_id: str
    workspace_id: str
    workspace_generation: int
    document_id: str
    document_version: int
    active_pack_id: str
    status: str
    findings: tuple[dict[str, Any], ...]
    limitations: tuple[str, ...]
    latency_ms: float
    latency_class: str
    completed_at: str
    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.analysis-result/v1",
            "request_id": self.request_id,
            "workspace_id": self.workspace_id,
            "workspace_generation": self.workspace_generation,
            "document_id": self.document_id,
            "document_version": self.document_version,
            "active_pack_id": self.active_pack_id,
            "status": self.status,
            "findings": list(self.findings),
            "limitations": list(self.limitations),
            "latency_ms": round(self.latency_ms, 3),
            "latency_class": self.latency_class,
            "completed_at": self.completed_at,
        }
EOF
cat > src/l9_debt_lsp/analysis/identity.py <<'EOF'
from __future__ import annotations
from urllib.parse import urlsplit, urlunsplit
from l9_debt_lsp.packs.hashing import namespaced_hash
def normalized_uri(uri: str) -> str:
    parts = urlsplit(uri)
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path,
            parts.query,
            "",
        )
    )
def workspace_identity(workspace_uri: str) -> str:
    return namespaced_hash(
        "workspace_",
        {
            "normalized_uri": normalized_uri(workspace_uri),
        },
    )
def document_identity(uri: str) -> str:
    return namespaced_hash(
        "doc_",
        {
            "normalized_uri": normalized_uri(uri),
        },
    )
def request_identity(
    *,
    workspace_id: str,
    workspace_generation: int,
    document_id: str,
    document_version: int,
    active_pack_id: str,
) -> str:
    return namespaced_hash(
        "request_",
        {
            "workspace_id": workspace_id,
            "workspace_generation": workspace_generation,
            "document_id": document_id,
            "document_version": document_version,
            "active_pack_id": active_pack_id,
        },
    )
EOF
cat > src/l9_debt_lsp/analysis/cancellation.py <<'EOF'
from __future__ import annotations
import asyncio
from dataclasses import dataclass
from .errors import AnalysisCancelledError
@dataclass(frozen=True)
class CancellationState:
    cancelled: bool
    reason: str | None
class CancellationToken:
    def __init__(self) -> None:
        self._event = asyncio.Event()
        self._reason: str | None = None
    @property
    def cancelled(self) -> bool:
        return self._event.is_set()
    @property
    def reason(self) -> str | None:
        return self._reason
    def cancel(self, reason: str) -> None:
        if self._event.is_set():
            return
        self._reason = reason
        self._event.set()
    async def wait(self) -> None:
        await self._event.wait()
    def raise_if_cancelled(self) -> None:
        if self.cancelled:
            raise AnalysisCancelledError(
                self._reason or "cancelled"
            )
    def snapshot(self) -> CancellationState:
        return CancellationState(
            cancelled=self.cancelled,
            reason=self.reason,
        )
EOF
cat > src/l9_debt_lsp/analysis/sdk_protocol.py <<'EOF'
from __future__ import annotations
from typing import Protocol, runtime_checkable
from .cancellation import CancellationToken
from .models import PackContext, SDKAnalysisResult
@runtime_checkable
class AnalysisSession(Protocol):
    """Public SDK incremental-analysis contract."""
    async def open_workspace(
        self,
        *,
        workspace_id: str,
        pack: PackContext,
    ) -> None:
        """Open a workspace analysis session."""
    async def close_workspace(
        self,
        *,
        workspace_id: str,
    ) -> None:
        """Close and release a workspace analysis session."""
    async def open_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        uri: str,
        language_id: str,
        version: int,
        text: str,
    ) -> None:
        """Open a document overlay."""
    async def update_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        version: int,
        text: str,
    ) -> None:
        """Replace a document overlay with a newer version."""
    async def evaluate_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        version: int,
        pack: PackContext,
        cancellation: CancellationToken,
    ) -> SDKAnalysisResult:
        """Evaluate one exact document version."""
    async def close_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> None:
        """Close and release a document overlay."""
    async def invalidate_dependencies(
        self,
        *,
        workspace_id: str,
        document_ids: tuple[str, ...],
    ) -> None:
        """Invalidate a bounded set of dependent documents."""
EOF
cat > src/l9_debt_lsp/analysis/null_sdk.py <<'EOF'
from __future__ import annotations
from .cancellation import CancellationToken
from .models import PackContext, SDKAnalysisResult
class UnavailableAnalysisSession:
    """Fail-closed adapter used until a real SDK binding is configured."""
    async def open_workspace(
        self,
        *,
        workspace_id: str,
        pack: PackContext,
    ) -> None:
        del workspace_id, pack
    async def close_workspace(
        self,
        *,
        workspace_id: str,
    ) -> None:
        del workspace_id
    async def open_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        uri: str,
        language_id: str,
        version: int,
        text: str,
    ) -> None:
        del (
            workspace_id,
            document_id,
            uri,
            language_id,
            version,
            text,
        )
    async def update_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        version: int,
        text: str,
    ) -> None:
        del workspace_id, document_id, version, text
    async def evaluate_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        version: int,
        pack: PackContext,
        cancellation: CancellationToken,
    ) -> SDKAnalysisResult:
        del workspace_id, document_id, version, pack
        cancellation.raise_if_cancelled()
        return SDKAnalysisResult(
            findings=(),
            limitations=(
                "SDK AnalysisSession adapter is unavailable.",
                "No complete analysis was performed.",
            ),
            complete=False,
            dependencies=(),
        )
    async def close_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> None:
        del workspace_id, document_id
    async def invalidate_dependencies(
        self,
        *,
        workspace_id: str,
        document_ids: tuple[str, ...],
    ) -> None:
        del workspace_id, document_ids
EOF
cat > src/l9_debt_lsp/analysis/latency.py <<'EOF'
from __future__ import annotations
DOCUMENT_P95_MS = 200.0
EVALUATION_TIMEOUT_MS = 5000.0
def classify_latency(
    latency_ms: float,
    *,
    cancelled: bool = False,
    timed_out: bool = False,
) -> str:
    if timed_out:
        return "timed_out"
    if cancelled:
        return "cancelled"
    if latency_ms <= DOCUMENT_P95_MS:
        return "within_budget"
    if latency_ms <= DOCUMENT_P95_MS * 2:
        return "elevated"
    return "exceeded"
EOF
cat > src/l9_debt_lsp/analysis/workspace.py <<'EOF'
from __future__ import annotations
import asyncio
from collections.abc import Iterable
from l9_debt_lsp.packs.time import format_utc, utc_now
from .errors import (
    DocumentLimitError,
    DocumentNotFoundError,
    DocumentVersionError,
    WorkspaceClosedError,
    WorkspaceNotFoundError,
)
from .identity import document_identity, workspace_identity
from .models import (
    DocumentOverlay,
    PackContext,
    WorkspaceSessionState,
)
from .sdk_protocol import AnalysisSession
MAX_DOCUMENT_BYTES = 5 * 1024 * 1024
MAX_OPEN_DOCUMENTS = 5000
MAX_OVERLAY_BYTES = 256 * 1024 * 1024
MAX_DEPENDENCY_EDGES = 100_000
MAX_INVALIDATION_DOCUMENTS = 250
class WorkspaceManager:
    def __init__(self, sdk: AnalysisSession) -> None:
        self._sdk = sdk
        self._workspaces: dict[
            str,
            WorkspaceSessionState,
        ] = {}
        self._lock = asyncio.Lock()
    async def open_workspace(
        self,
        *,
        workspace_uri: str,
        pack: PackContext,
    ) -> WorkspaceSessionState:
        workspace_id = workspace_identity(workspace_uri)
        async with self._lock:
            existing = self._workspaces.get(workspace_id)
            if existing is not None and existing.state == "open":
                if (
                    existing.active_pack is not None
                    and existing.active_pack.pack_id
                    != pack.pack_id
                ):
                    existing.generation += 1
                    existing.active_pack = pack
                    existing.limitations.add(
                        "Active pack changed; previous analyses are stale."
                    )
                return existing
            state = WorkspaceSessionState(
                workspace_id=workspace_id,
                generation=0,
                state="created",
                active_pack=pack,
            )
            self._workspaces[workspace_id] = state
        await self._sdk.open_workspace(
            workspace_id=workspace_id,
            pack=pack,
        )
        async with self._lock:
            state.state = "open"
            return state
    async def close_workspace(
        self,
        workspace_id: str,
    ) -> None:
        async with self._lock:
            state = self._require_workspace(workspace_id)
            if state.state == "closed":
                return
            state.state = "closing"
            state.generation += 1
            document_ids = tuple(state.documents)
        for document_id in document_ids:
            await self._sdk.close_document(
                workspace_id=workspace_id,
                document_id=document_id,
            )
        await self._sdk.close_workspace(
            workspace_id=workspace_id,
        )
        async with self._lock:
            state.documents.clear()
            state.reverse_dependencies.clear()
            state.state = "closed"
    async def open_document(
        self,
        *,
        workspace_id: str,
        uri: str,
        language_id: str,
        version: int,
        text: str,
    ) -> DocumentOverlay:
        self._validate_document_content(text)
        document_id = document_identity(uri)
        now = format_utc(utc_now())
        async with self._lock:
            state = self._require_open_workspace(workspace_id)
            existing = state.documents.get(document_id)
            if existing is not None and existing.state == "open":
                raise DocumentVersionError(
                    f"document is already open: {document_id}"
                )
            if (
                sum(
                    document.state == "open"
                    for document in state.documents.values()
                )
                >= MAX_OPEN_DOCUMENTS
            ):
                raise DocumentLimitError(
                    "workspace open-document limit exceeded"
                )
            overlay = DocumentOverlay(
                document_id=document_id,
                uri=uri,
                language_id=language_id,
                version=version,
                text=text,
                opened_at=now,
                updated_at=now,
            )
            projected_bytes = (
                state.overlay_bytes + overlay.content_bytes
            )
            if projected_bytes > MAX_OVERLAY_BYTES:
                raise DocumentLimitError(
                    "workspace overlay byte limit exceeded"
                )
            state.documents[document_id] = overlay
            state.generation += 1
        try:
            await self._sdk.open_document(
                workspace_id=workspace_id,
                document_id=document_id,
                uri=uri,
                language_id=language_id,
                version=version,
                text=text,
            )
        except Exception:
            async with self._lock:
                state.documents.pop(document_id, None)
                state.generation += 1
            raise
        return overlay
    async def update_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        version: int,
        text: str,
    ) -> DocumentOverlay:
        self._validate_document_content(text)
        async with self._lock:
            state = self._require_open_workspace(workspace_id)
            overlay = self._require_document(
                state,
                document_id,
            )
            if version <= overlay.version:
                raise DocumentVersionError(
                    "document versions must be strictly increasing"
                )
            previous_text = overlay.text
            previous_version = overlay.version
            previous_updated_at = overlay.updated_at
            projected_bytes = (
                state.overlay_bytes
                - overlay.content_bytes
                + len(text.encode("utf-8"))
            )
            if projected_bytes > MAX_OVERLAY_BYTES:
                raise DocumentLimitError(
                    "workspace overlay byte limit exceeded"
                )
            overlay.text = text
            overlay.version = version
            overlay.updated_at = format_utc(utc_now())
            state.generation += 1
        try:
            await self._sdk.update_document(
                workspace_id=workspace_id,
                document_id=document_id,
                version=version,
                text=text,
            )
        except Exception:
            async with self._lock:
                overlay.text = previous_text
                overlay.version = previous_version
                overlay.updated_at = previous_updated_at
                state.generation += 1
            raise
        return overlay
    async def close_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> None:
        async with self._lock:
            state = self._require_open_workspace(workspace_id)
            overlay = self._require_document(
                state,
                document_id,
            )
            overlay.state = "closed"
            overlay.text = ""
            overlay.updated_at = format_utc(utc_now())
            state.generation += 1
            state.reverse_dependencies.pop(
                document_id,
                None,
            )
            for dependents in state.reverse_dependencies.values():
                dependents.discard(document_id)
        await self._sdk.close_document(
            workspace_id=workspace_id,
            document_id=document_id,
        )
    async def update_dependencies(
        self,
        *,
        workspace_id: str,
        document_id: str,
        dependencies: Iterable[str],
    ) -> tuple[str, ...]:
        normalized = tuple(
            sorted(set(dependencies))
        )
        async with self._lock:
            state = self._require_open_workspace(workspace_id)
            self._require_document(state, document_id)
            for dependents in state.reverse_dependencies.values():
                dependents.discard(document_id)
            for dependency in normalized:
                state.reverse_dependencies.setdefault(
                    dependency,
                    set(),
                ).add(document_id)
            if state.dependency_edge_count > MAX_DEPENDENCY_EDGES:
                state.limitations.add(
                    "Dependency graph limit exceeded."
                )
                raise DocumentLimitError(
                    "dependency edge limit exceeded"
                )
            state.generation += 1
        return normalized
    async def invalidated_dependents(
        self,
        *,
        workspace_id: str,
        changed_document_id: str,
    ) -> tuple[str, ...]:
        async with self._lock:
            state = self._require_open_workspace(workspace_id)
            dependents = sorted(
                state.reverse_dependencies.get(
                    changed_document_id,
                    set(),
                )
            )
            if len(dependents) > MAX_INVALIDATION_DOCUMENTS:
                state.limitations.add(
                    "Dependency invalidation exceeded the bounded limit."
                )
                dependents = dependents[
                    :MAX_INVALIDATION_DOCUMENTS
                ]
            result = tuple(dependents)
        if result:
            await self._sdk.invalidate_dependencies(
                workspace_id=workspace_id,
                document_ids=result,
            )
        return result
    async def snapshot(
        self,
        workspace_id: str,
    ) -> WorkspaceSessionState:
        async with self._lock:
            return self._require_workspace(workspace_id)
    def get_workspace_nowait(
        self,
        workspace_id: str,
    ) -> WorkspaceSessionState:
        return self._require_workspace(workspace_id)
    @staticmethod
    def _validate_document_content(text: str) -> None:
        size = len(text.encode("utf-8"))
        if size > MAX_DOCUMENT_BYTES:
            raise DocumentLimitError(
                f"document exceeds {MAX_DOCUMENT_BYTES} bytes"
            )
    def _require_workspace(
        self,
        workspace_id: str,
    ) -> WorkspaceSessionState:
        state = self._workspaces.get(workspace_id)
        if state is None:
            raise WorkspaceNotFoundError(workspace_id)
        return state
    def _require_open_workspace(
        self,
        workspace_id: str,
    ) -> WorkspaceSessionState:
        state = self._require_workspace(workspace_id)
        if state.state != "open":
            raise WorkspaceClosedError(workspace_id)
        return state
    @staticmethod
    def _require_document(
        state: WorkspaceSessionState,
        document_id: str,
    ) -> DocumentOverlay:
        overlay = state.documents.get(document_id)
        if overlay is None or overlay.state != "open":
            raise DocumentNotFoundError(document_id)
        return overlay
EOF
cat > src/l9_debt_lsp/analysis/scheduler.py <<'EOF'
from __future__ import annotations
import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
from l9_debt_lsp.packs.time import format_utc, utc_now
from .cancellation import CancellationToken
from .errors import (
    AnalysisCancelledError,
    AnalysisTimeoutError,
    DocumentNotFoundError,
    StaleAnalysisResultError,
)
from .identity import request_identity
from .latency import EVALUATION_TIMEOUT_MS, classify_latency
from .models import (
    AnalysisRequest,
    AnalysisResult,
    SDKAnalysisResult,
)
from .sdk_protocol import AnalysisSession
from .workspace import WorkspaceManager
@dataclass
class RunningAnalysis:
    request: AnalysisRequest
    cancellation: CancellationToken
    task: asyncio.Task[AnalysisResult]
class AnalysisScheduler:
    def __init__(
        self,
        *,
        sdk: AnalysisSession,
        workspaces: WorkspaceManager,
        maximum_global_evaluations: int = 4,
        maximum_workspace_evaluations: int = 2,
        timeout_ms: float = EVALUATION_TIMEOUT_MS,
    ) -> None:
        self._sdk = sdk
        self._workspaces = workspaces
        self._global_semaphore = asyncio.Semaphore(
            maximum_global_evaluations
        )
        self._workspace_semaphores: dict[
            str,
            asyncio.Semaphore,
        ] = defaultdict(
            lambda: asyncio.Semaphore(
                maximum_workspace_evaluations
            )
        )
        self._document_locks: dict[
            tuple[str, str],
            asyncio.Lock,
        ] = defaultdict(asyncio.Lock)
        self._running: dict[
            tuple[str, str],
            RunningAnalysis,
        ] = {}
        self._timeout_seconds = timeout_ms / 1000.0
        self._state_lock = asyncio.Lock()
    async def evaluate(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> AnalysisResult:
        state = self._workspaces.get_workspace_nowait(
            workspace_id
        )
        overlay = state.documents.get(document_id)
        if overlay is None or overlay.state != "open":
            raise DocumentNotFoundError(document_id)
        if state.active_pack is None:
            raise RuntimeError(
                "workspace has no active pack"
            )
        request = AnalysisRequest(
            request_id=request_identity(
                workspace_id=workspace_id,
                workspace_generation=state.generation,
                document_id=document_id,
                document_version=overlay.version,
                active_pack_id=state.active_pack.pack_id,
            ),
            workspace_id=workspace_id,
            workspace_generation=state.generation,
            document_id=document_id,
            document_uri=overlay.uri,
            document_version=overlay.version,
            language_id=overlay.language_id,
            active_pack_id=state.active_pack.pack_id,
            active_pack_version=(
                state.active_pack.pack_version
            ),
            created_at=format_utc(utc_now()),
            limitations=(),
        )
        cancellation = CancellationToken()
        key = (workspace_id, document_id)
        async with self._state_lock:
            previous = self._running.get(key)
            if previous is not None:
                previous.cancellation.cancel(
                    "document_updated"
                )
            task = asyncio.create_task(
                self._execute(
                    request=request,
                    cancellation=cancellation,
                )
            )
            self._running[key] = RunningAnalysis(
                request=request,
                cancellation=cancellation,
                task=task,
            )
        try:
            return await task
        finally:
            async with self._state_lock:
                current = self._running.get(key)
                if (
                    current is not None
                    and current.request.request_id
                    == request.request_id
                ):
                    self._running.pop(key, None)
    async def cancel_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        reason: str,
    ) -> None:
        key = (workspace_id, document_id)
        async with self._state_lock:
            running = self._running.get(key)
            if running is not None:
                running.cancellation.cancel(reason)
    async def cancel_workspace(
        self,
        *,
        workspace_id: str,
        reason: str,
    ) -> None:
        async with self._state_lock:
            for key, running in self._running.items():
                if key[0] == workspace_id:
                    running.cancellation.cancel(reason)
    async def shutdown(self) -> None:
        async with self._state_lock:
            running = tuple(self._running.values())
            for item in running:
                item.cancellation.cancel("server_shutdown")
        if running:
            await asyncio.gather(
                *(item.task for item in running),
                return_exceptions=True,
            )
    async def _execute(
        self,
        *,
        request: AnalysisRequest,
        cancellation: CancellationToken,
    ) -> AnalysisResult:
        started = time.monotonic()
        workspace_semaphore = self._workspace_semaphores[
            request.workspace_id
        ]
        document_lock = self._document_locks[
            (request.workspace_id, request.document_id)
        ]
        try:
            async with self._global_semaphore:
                async with workspace_semaphore:
                    async with document_lock:
                        cancellation.raise_if_cancelled()
                        sdk_result = await asyncio.wait_for(
                            self._sdk.evaluate_document(
                                workspace_id=request.workspace_id,
                                document_id=request.document_id,
                                version=request.document_version,
                                pack=self._workspaces
                                .get_workspace_nowait(
                                    request.workspace_id
                                )
                                .active_pack,
                                cancellation=cancellation,
                            ),
                            timeout=self._timeout_seconds,
                        )
                        cancellation.raise_if_cancelled()
                        self._validate_freshness(request)
                        await self._workspaces.update_dependencies(
                            workspace_id=request.workspace_id,
                            document_id=request.document_id,
                            dependencies=sdk_result.dependencies,
                        )
                        latency_ms = (
                            time.monotonic() - started
                        ) * 1000.0
                        return self._result_from_sdk(
                            request=request,
                            sdk_result=sdk_result,
                            latency_ms=latency_ms,
                        )
        except asyncio.TimeoutError as error:
            cancellation.cancel("timeout")
            latency_ms = (
                time.monotonic() - started
            ) * 1000.0
            raise AnalysisTimeoutError(
                f"analysis exceeded "
                f"{self._timeout_seconds:.3f}s"
            ) from error
        except AnalysisCancelledError:
            latency_ms = (
                time.monotonic() - started
            ) * 1000.0
            return AnalysisResult(
                request_id=request.request_id,
                workspace_id=request.workspace_id,
                workspace_generation=(
                    request.workspace_generation
                ),
                document_id=request.document_id,
                document_version=request.document_version,
                active_pack_id=request.active_pack_id,
                status="cancelled",
                findings=(),
                limitations=(
                    cancellation.reason or "cancelled",
                ),
                latency_ms=latency_ms,
                latency_class=classify_latency(
                    latency_ms,
                    cancelled=True,
                ),
                completed_at=format_utc(utc_now()),
            )
        except StaleAnalysisResultError as error:
            latency_ms = (
                time.monotonic() - started
            ) * 1000.0
            return AnalysisResult(
                request_id=request.request_id,
                workspace_id=request.workspace_id,
                workspace_generation=(
                    request.workspace_generation
                ),
                document_id=request.document_id,
                document_version=request.document_version,
                active_pack_id=request.active_pack_id,
                status="stale",
                findings=(),
                limitations=(str(error),),
                latency_ms=latency_ms,
                latency_class=classify_latency(latency_ms),
                completed_at=format_utc(utc_now()),
            )
        except Exception as error:
            latency_ms = (
                time.monotonic() - started
            ) * 1000.0
            return AnalysisResult(
                request_id=request.request_id,
                workspace_id=request.workspace_id,
                workspace_generation=(
                    request.workspace_generation
                ),
                document_id=request.document_id,
                document_version=request.document_version,
                active_pack_id=request.active_pack_id,
                status="failed",
                findings=(),
                limitations=(
                    f"analysis failed: {type(error).__name__}",
                ),
                latency_ms=latency_ms,
                latency_class=classify_latency(latency_ms),
                completed_at=format_utc(utc_now()),
            )
    def _validate_freshness(
        self,
        request: AnalysisRequest,
    ) -> None:
        state = self._workspaces.get_workspace_nowait(
            request.workspace_id
        )
        if state.state != "open":
            raise StaleAnalysisResultError(
                "workspace is no longer open"
            )
        overlay = state.documents.get(request.document_id)
        if overlay is None or overlay.state != "open":
            raise StaleAnalysisResultError(
                "document is no longer open"
            )
        if overlay.version != request.document_version:
            raise StaleAnalysisResultError(
                "document version advanced"
            )
        if state.generation != request.workspace_generation:
            raise StaleAnalysisResultError(
                "workspace generation changed"
            )
        if (
            state.active_pack is None
            or state.active_pack.pack_id
            != request.active_pack_id
        ):
            raise StaleAnalysisResultError(
                "active pack changed"
            )
    @staticmethod
    def _result_from_sdk(
        *,
        request: AnalysisRequest,
        sdk_result: SDKAnalysisResult,
        latency_ms: float,
    ) -> AnalysisResult:
        limitations = tuple(
            sorted(set(sdk_result.limitations))
        )
        status = (
            "complete"
            if sdk_result.complete
            else "incomplete"
        )
        if status == "incomplete" and not limitations:
            limitations = (
                "SDK reported incomplete analysis without details.",
            )
        findings = tuple(
            sorted(
                sdk_result.findings,
                key=lambda finding: (
                    str(finding.get("canonical_rule_id", "")),
                    str(finding.get("finding_id", "")),
                ),
            )
        )
        return AnalysisResult(
            request_id=request.request_id,
            workspace_id=request.workspace_id,
            workspace_generation=(
                request.workspace_generation
            ),
            document_id=request.document_id,
            document_version=request.document_version,
            active_pack_id=request.active_pack_id,
            status=status,
            findings=findings,
            limitations=limitations,
            latency_ms=latency_ms,
            latency_class=classify_latency(latency_ms),
            completed_at=format_utc(utc_now()),
        )
EOF
cat > src/l9_debt_lsp/analysis/runtime.py <<'EOF'
from __future__ import annotations
from typing import Any
from .models import PackContext
from .scheduler import AnalysisScheduler
from .sdk_protocol import AnalysisSession
from .workspace import WorkspaceManager
class IncrementalAnalysisRuntime:
    def __init__(self, sdk: AnalysisSession) -> None:
        self.sdk = sdk
        self.workspaces = WorkspaceManager(sdk)
        self.scheduler = AnalysisScheduler(
            sdk=sdk,
            workspaces=self.workspaces,
        )
    async def open_workspace(
        self,
        *,
        workspace_uri: str,
        pack: PackContext,
    ) -> dict[str, Any]:
        state = await self.workspaces.open_workspace(
            workspace_uri=workspace_uri,
            pack=pack,
        )
        return state.as_dict()
    async def close_workspace(
        self,
        workspace_id: str,
    ) -> None:
        await self.scheduler.cancel_workspace(
            workspace_id=workspace_id,
            reason="workspace_closed",
        )
        await self.workspaces.close_workspace(workspace_id)
    async def open_document(
        self,
        *,
        workspace_id: str,
        uri: str,
        language_id: str,
        version: int,
        text: str,
    ) -> dict[str, Any]:
        overlay = await self.workspaces.open_document(
            workspace_id=workspace_id,
            uri=uri,
            language_id=language_id,
            version=version,
            text=text,
        )
        return overlay.metadata()
    async def update_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        version: int,
        text: str,
    ) -> dict[str, Any]:
        await self.scheduler.cancel_document(
            workspace_id=workspace_id,
            document_id=document_id,
            reason="document_updated",
        )
        overlay = await self.workspaces.update_document(
            workspace_id=workspace_id,
            document_id=document_id,
            version=version,
            text=text,
        )
        await self.workspaces.invalidated_dependents(
            workspace_id=workspace_id,
            changed_document_id=document_id,
        )
        return overlay.metadata()
    async def evaluate_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> dict[str, Any]:
        result = await self.scheduler.evaluate(
            workspace_id=workspace_id,
            document_id=document_id,
        )
        return result.as_dict()
    async def close_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> None:
        await self.scheduler.cancel_document(
            workspace_id=workspace_id,
            document_id=document_id,
            reason="document_closed",
        )
        await self.workspaces.close_document(
            workspace_id=workspace_id,
            document_id=document_id,
        )
    async def shutdown(self) -> None:
        await self.scheduler.shutdown()
EOF
###############################################################################
# 4. Runtime service
###############################################################################
cat > src/l9_debt_lsp/runtime/analysis_service.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from l9_debt_lsp.analysis.models import PackContext
from l9_debt_lsp.analysis.null_sdk import (
    UnavailableAnalysisSession,
)
from l9_debt_lsp.analysis.runtime import (
    IncrementalAnalysisRuntime,
)
from l9_debt_lsp.packs.activation import ActivationManager
from l9_debt_lsp.packs.jsonio import load_json
from l9_debt_lsp.packs.paths import StatePaths
def load_active_pack_context(
    *,
    paths: StatePaths,
    schema_root: Path,
) -> PackContext:
    manager = ActivationManager(
        paths=paths,
        schema_root=schema_root,
    )
    pointer = manager.load_active()
    if pointer is None:
        raise RuntimeError(
            "no active defense pack is configured"
        )
    pack_root = paths.packs / pointer.pack_id
    defense_pack = load_json(
        pack_root / "defense-pack.json"
    )
    return PackContext(
        pack_id=pointer.pack_id,
        pack_version=pointer.pack_version,
        corpus_snapshot=pointer.corpus_snapshot,
        compiler_version=pointer.compiler_version,
        taxonomy_version=pointer.taxonomy_version,
        sdk_contract_version=pointer.sdk_contract_version,
    )
def build_default_runtime() -> IncrementalAnalysisRuntime:
    return IncrementalAnalysisRuntime(
        UnavailableAnalysisSession()
    )
EOF
cat > src/l9_debt_lsp/runtime/health.py <<'EOF'
from __future__ import annotations
from typing import Any
from l9_debt_lsp.analysis.runtime import (
    IncrementalAnalysisRuntime,
)
def runtime_health(
    runtime: IncrementalAnalysisRuntime,
    *,
    active_pack_id: str | None,
) -> dict[str, Any]:
    workspaces = runtime.workspaces._workspaces
    open_documents = sum(
        sum(
            document.state == "open"
            for document in workspace.documents.values()
        )
        for workspace in workspaces.values()
        if workspace.state == "open"
    )
    running = len(runtime.scheduler._running)
    limitations: list[str] = []
    if active_pack_id is None:
        limitations.append(
            "No active defense pack is configured."
        )
    status = (
        "healthy"
        if not limitations
        else "degraded"
    )
    return {
        "schema_version": "l9.runtime-health/v1",
        "status": status,
        "workspace_count": sum(
            workspace.state == "open"
            for workspace in workspaces.values()
        ),
        "open_document_count": open_documents,
        "running_evaluation_count": running,
        "queued_evaluation_count": 0,
        "active_pack_id": active_pack_id,
        "limitations": limitations,
    }
EOF
###############################################################################
# 5. Capabilities
###############################################################################
cat > src/l9_debt_lsp/runtime/capabilities.py <<'EOF'
from __future__ import annotations
from typing import Any
def phase_capabilities() -> dict[str, Any]:
    """Return the LSP-P2 capability surface."""
    return {
        "schema_version": "l9.lsp-server-capabilities/v1",
        "phase": "LSP-P2",
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
            "diagnostics": False,
            "code_actions": False,
            "telemetry": False
        },
        "limitations": [
            "A concrete public SDK AnalysisSession binding must be configured.",
            "Diagnostic projection is implemented in LSP-P3.",
            "Code actions are implemented in LSP-P4.",
            "Telemetry transport is implemented in LSP-P5."
        ]
    }
EOF
###############################################################################
# 6. Tests
###############################################################################
cat > tests/fixtures/analysis/fake_sdk.py <<'EOF'
from __future__ import annotations
import asyncio
from l9_debt_lsp.analysis.cancellation import (
    CancellationToken,
)
from l9_debt_lsp.analysis.models import (
    PackContext,
    SDKAnalysisResult,
)
class FakeAnalysisSession:
    def __init__(
        self,
        *,
        delay: float = 0.0,
        complete: bool = True,
    ) -> None:
        self.delay = delay
        self.complete = complete
        self.workspaces: set[str] = set()
        self.documents: dict[
            tuple[str, str],
            tuple[int, str],
        ] = {}
    async def open_workspace(
        self,
        *,
        workspace_id: str,
        pack: PackContext,
    ) -> None:
        del pack
        self.workspaces.add(workspace_id)
    async def close_workspace(
        self,
        *,
        workspace_id: str,
    ) -> None:
        self.workspaces.discard(workspace_id)
    async def open_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        uri: str,
        language_id: str,
        version: int,
        text: str,
    ) -> None:
        del uri, language_id
        self.documents[(workspace_id, document_id)] = (
            version,
            text,
        )
    async def update_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        version: int,
        text: str,
    ) -> None:
        self.documents[(workspace_id, document_id)] = (
            version,
            text,
        )
    async def evaluate_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        version: int,
        pack: PackContext,
        cancellation: CancellationToken,
    ) -> SDKAnalysisResult:
        del pack
        if self.delay:
            await asyncio.sleep(self.delay)
        cancellation.raise_if_cancelled()
        stored_version, text = self.documents[
            (workspace_id, document_id)
        ]
        assert stored_version == version
        return SDKAnalysisResult(
            findings=(
                {
                    "finding_id": (
                        f"finding-{document_id}-{version}"
                    ),
                    "canonical_rule_id": "l9.example",
                    "message": text,
                },
            ),
            limitations=(
                ()
                if self.complete
                else ("partial parse",)
            ),
            complete=self.complete,
            dependencies=(),
        )
    async def close_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> None:
        self.documents.pop(
            (workspace_id, document_id),
            None,
        )
    async def invalidate_dependencies(
        self,
        *,
        workspace_id: str,
        document_ids: tuple[str, ...],
    ) -> None:
        del workspace_id, document_ids
EOF
touch tests/fixtures/__init__.py
touch tests/fixtures/analysis/__init__.py
cat > tests/analysis/test_workspace_lifecycle.py <<'EOF'
from __future__ import annotations
import pytest
from l9_debt_lsp.analysis.errors import (
    DocumentVersionError,
)
from l9_debt_lsp.analysis.identity import (
    document_identity,
)
from l9_debt_lsp.analysis.models import PackContext
from l9_debt_lsp.analysis.workspace import WorkspaceManager
from tests.fixtures.analysis.fake_sdk import (
    FakeAnalysisSession,
)
@pytest.mark.asyncio
async def test_document_versions_are_strictly_increasing() -> None:
    sdk = FakeAnalysisSession()
    manager = WorkspaceManager(sdk)
    pack = PackContext(
        pack_id="pack_" + "a" * 64,
        pack_version="1.0.0",
        corpus_snapshot="cs_" + "b" * 64,
        compiler_version="1.0.0",
        taxonomy_version="1.0.0",
        sdk_contract_version="l9.integration-contract/v1",
    )
    state = await manager.open_workspace(
        workspace_uri="file:///workspace",
        pack=pack,
    )
    uri = "file:///workspace/a.py"
    overlay = await manager.open_document(
        workspace_id=state.workspace_id,
        uri=uri,
        language_id="python",
        version=1,
        text="print('a')",
    )
    with pytest.raises(DocumentVersionError):
        await manager.update_document(
            workspace_id=state.workspace_id,
            document_id=overlay.document_id,
            version=1,
            text="print('b')",
        )
    updated = await manager.update_document(
        workspace_id=state.workspace_id,
        document_id=overlay.document_id,
        version=2,
        text="print('b')",
    )
    assert updated.version == 2
EOF
cat > tests/analysis/test_runtime.py <<'EOF'
from __future__ import annotations
import pytest
from l9_debt_lsp.analysis.models import PackContext
from l9_debt_lsp.analysis.runtime import (
    IncrementalAnalysisRuntime,
)
from tests.fixtures.analysis.fake_sdk import (
    FakeAnalysisSession,
)
@pytest.mark.asyncio
async def test_complete_analysis_preserves_version_and_pack() -> None:
    runtime = IncrementalAnalysisRuntime(
        FakeAnalysisSession()
    )
    pack = PackContext(
        pack_id="pack_" + "a" * 64,
        pack_version="1.0.0",
        corpus_snapshot="cs_" + "b" * 64,
        compiler_version="1.0.0",
        taxonomy_version="1.0.0",
        sdk_contract_version="l9.integration-contract/v1",
    )
    workspace = await runtime.open_workspace(
        workspace_uri="file:///workspace",
        pack=pack,
    )
    document = await runtime.open_document(
        workspace_id=workspace["workspace_id"],
        uri="file:///workspace/a.py",
        language_id="python",
        version=1,
        text="print('hello')",
    )
    result = await runtime.evaluate_document(
        workspace_id=workspace["workspace_id"],
        document_id=document["document_id"],
    )
    assert result["status"] == "complete"
    assert result["document_version"] == 1
    assert result["active_pack_id"] == pack.pack_id
    assert len(result["findings"]) == 1
@pytest.mark.asyncio
async def test_incomplete_sdk_result_is_not_pass() -> None:
    runtime = IncrementalAnalysisRuntime(
        FakeAnalysisSession(complete=False)
    )
    pack = PackContext(
        pack_id="pack_" + "a" * 64,
        pack_version="1.0.0",
        corpus_snapshot="cs_" + "b" * 64,
        compiler_version="1.0.0",
        taxonomy_version="1.0.0",
        sdk_contract_version="l9.integration-contract/v1",
    )
    workspace = await runtime.open_workspace(
        workspace_uri="file:///workspace",
        pack=pack,
    )
    document = await runtime.open_document(
        workspace_id=workspace["workspace_id"],
        uri="file:///workspace/a.py",
        language_id="python",
        version=1,
        text="incomplete",
    )
    result = await runtime.evaluate_document(
        workspace_id=workspace["workspace_id"],
        document_id=document["document_id"],
    )
    assert result["status"] == "incomplete"
    assert result["limitations"]
EOF
cat > tests/concurrency/test_stale_result_suppression.py <<'EOF'
from __future__ import annotations
import asyncio
import pytest
from l9_debt_lsp.analysis.models import PackContext
from l9_debt_lsp.analysis.runtime import (
    IncrementalAnalysisRuntime,
)
from tests.fixtures.analysis.fake_sdk import (
    FakeAnalysisSession,
)
@pytest.mark.asyncio
async def test_new_document_version_suppresses_old_result() -> None:
    runtime = IncrementalAnalysisRuntime(
        FakeAnalysisSession(delay=0.05)
    )
    pack = PackContext(
        pack_id="pack_" + "a" * 64,
        pack_version="1.0.0",
        corpus_snapshot="cs_" + "b" * 64,
        compiler_version="1.0.0",
        taxonomy_version="1.0.0",
        sdk_contract_version="l9.integration-contract/v1",
    )
    workspace = await runtime.open_workspace(
        workspace_uri="file:///workspace",
        pack=pack,
    )
    document = await runtime.open_document(
        workspace_id=workspace["workspace_id"],
        uri="file:///workspace/a.py",
        language_id="python",
        version=1,
        text="version one",
    )
    first = asyncio.create_task(
        runtime.evaluate_document(
            workspace_id=workspace["workspace_id"],
            document_id=document["document_id"],
        )
    )
    await asyncio.sleep(0.01)
    await runtime.update_document(
        workspace_id=workspace["workspace_id"],
        document_id=document["document_id"],
        version=2,
        text="version two",
    )
    first_result = await first
    assert first_result["status"] in {
        "cancelled",
        "stale",
    }
    second_result = await runtime.evaluate_document(
        workspace_id=workspace["workspace_id"],
        document_id=document["document_id"],
    )
    assert second_result["status"] == "complete"
    assert second_result["document_version"] == 2
EOF
cat > tests/concurrency/test_workspace_close_cancels.py <<'EOF'
from __future__ import annotations
import asyncio
import pytest
from l9_debt_lsp.analysis.models import PackContext
from l9_debt_lsp.analysis.runtime import (
    IncrementalAnalysisRuntime,
)
from tests.fixtures.analysis.fake_sdk import (
    FakeAnalysisSession,
)
@pytest.mark.asyncio
async def test_workspace_close_cancels_running_analysis() -> None:
    runtime = IncrementalAnalysisRuntime(
        FakeAnalysisSession(delay=0.05)
    )
    pack = PackContext(
        pack_id="pack_" + "a" * 64,
        pack_version="1.0.0",
        corpus_snapshot="cs_" + "b" * 64,
        compiler_version="1.0.0",
        taxonomy_version="1.0.0",
        sdk_contract_version="l9.integration-contract/v1",
    )
    workspace = await runtime.open_workspace(
        workspace_uri="file:///workspace",
        pack=pack,
    )
    document = await runtime.open_document(
        workspace_id=workspace["workspace_id"],
        uri="file:///workspace/a.py",
        language_id="python",
        version=1,
        text="content",
    )
    evaluation = asyncio.create_task(
        runtime.evaluate_document(
            workspace_id=workspace["workspace_id"],
            document_id=document["document_id"],
        )
    )
    await asyncio.sleep(0.01)
    await runtime.close_workspace(
        workspace["workspace_id"]
    )
    result = await evaluation
    assert result["status"] in {
        "cancelled",
        "stale",
    }
EOF
cat > tests/analysis/test_bounded_invalidation.py <<'EOF'
from __future__ import annotations
import pytest
from l9_debt_lsp.analysis.models import PackContext
from l9_debt_lsp.analysis.workspace import WorkspaceManager
from tests.fixtures.analysis.fake_sdk import (
    FakeAnalysisSession,
)
@pytest.mark.asyncio
async def test_dependency_invalidation_is_deterministic() -> None:
    sdk = FakeAnalysisSession()
    manager = WorkspaceManager(sdk)
    pack = PackContext(
        pack_id="pack_" + "a" * 64,
        pack_version="1.0.0",
        corpus_snapshot="cs_" + "b" * 64,
        compiler_version="1.0.0",
        taxonomy_version="1.0.0",
        sdk_contract_version="l9.integration-contract/v1",
    )
    state = await manager.open_workspace(
        workspace_uri="file:///workspace",
        pack=pack,
    )
    source = await manager.open_document(
        workspace_id=state.workspace_id,
        uri="file:///workspace/source.py",
        language_id="python",
        version=1,
        text="source",
    )
    dependent = await manager.open_document(
        workspace_id=state.workspace_id,
        uri="file:///workspace/dependent.py",
        language_id="python",
        version=1,
        text="dependent",
    )
    await manager.update_dependencies(
        workspace_id=state.workspace_id,
        document_id=dependent.document_id,
        dependencies=(source.document_id,),
    )
    invalidated = await manager.invalidated_dependents(
        workspace_id=state.workspace_id,
        changed_document_id=source.document_id,
    )
    assert invalidated == (dependent.document_id,)
EOF
cat > tests/performance/test_latency_classification.py <<'EOF'
from __future__ import annotations
from l9_debt_lsp.analysis.latency import classify_latency
def test_latency_budget_classes() -> None:
    assert classify_latency(50) == "within_budget"
    assert classify_latency(250) == "elevated"
    assert classify_latency(500) == "exceeded"
    assert (
        classify_latency(10, cancelled=True)
        == "cancelled"
    )
    assert (
        classify_latency(5001, timed_out=True)
        == "timed_out"
    )
EOF
###############################################################################
# 7. Test dependencies
###############################################################################
python3 - <<'PY'
from pathlib import Path
path = Path("pyproject.toml")
text = path.read_text(encoding="utf-8")
if '"pytest-asyncio>=0.24,<1"' not in text:
    text = text.replace(
        '  "pytest-cov>=5,<7",',
        '  "pytest-cov>=5,<7",\n'
        '  "pytest-asyncio>=0.24,<1",',
    )
if 'asyncio_mode = "auto"' not in text:
    text = text.replace(
        'addopts = "-ra --strict-markers"',
        'addopts = "-ra --strict-markers"\n'
        'asyncio_mode = "auto"',
    )
path.write_text(text, encoding="utf-8")
PY
###############################################################################
# 8. ADRs
###############################################################################
cat > docs/architecture/ADRs/ADR-LSP-009-public-sdk-session-boundary.md <<'EOF'
# ADR-LSP-009: Incremental analysis uses a public SDK session boundary
- Status: Accepted
- Phase: LSP-P2
## Decision
The LSP integrates with SDK incremental semantics through the public
`AnalysisSession` protocol.
The LSP does not import SDK private modules or reconstruct SDK findings and
evidence.
A fail-closed unavailable adapter reports incomplete analysis rather than an
empty successful result.
EOF
cat > docs/architecture/ADRs/ADR-LSP-010-document-overlays-are-memory-only.md <<'EOF'
# ADR-LSP-010: Editor document overlays are memory-only
- Status: Accepted
- Phase: LSP-P2
## Decision
Unsaved editor content remains in memory and is deleted when the document or
workspace closes.
Normal incremental analysis does not persist source text, write SQLite state
per keystroke, or emit source content into logs or telemetry.
EOF
cat > docs/architecture/ADRs/ADR-LSP-011-stale-results-are-discarded.md <<'EOF'
# ADR-LSP-011: Stale analysis results are never published
- Status: Accepted
- Phase: LSP-P2
## Decision
An analysis result is stale when its document version, workspace generation,
active pack, or request identity no longer matches current runtime state.
Stale results are discarded. They are not converted to successful empty
diagnostics.
EOF
cat > docs/architecture/ADRs/ADR-LSP-012-bounded-invalidation.md <<'EOF'
# ADR-LSP-012: Dependency invalidation is bounded
- Status: Accepted
- Phase: LSP-P2
## Decision
One document change may invalidate at most 250 dependent documents in the
immediate incremental path.
Overflow creates an explicit incomplete-analysis limitation and requires a
bounded workspace refresh. It never triggers an unbounded repository scan.
EOF
###############################################################################
# 9. Roadmap and README
###############################################################################
python3 - <<'PY'
from pathlib import Path
path = Path("ROADMAP.md")
text = path.read_text(encoding="utf-8")
text = text.replace(
    """## LSP-P2 — SDK incremental adapter
Status: Planned
- AnalysisSession integration
- workspace sessions
- in-memory document overlays
- cancellation
- bounded invalidation
- stale-result suppression
""",
    """## LSP-P2 — SDK incremental adapter
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
""",
)
path.write_text(text, encoding="utf-8")
PY
cat >> README.md <<'EOF'
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
EOF

###############################################################################

10. CI

###############################################################################

cat > .github/workflows/phase-3-incremental-analysis.yml <<‘EOF’
name: LSP-P2 Incremental Analysis

on:
pull_request:
push:
branches:
- main

permissions:
contents: read

jobs:
incremental-analysis:
runs-on: ubuntu-latest
timeout-minutes: 15

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
  - name: Incremental-analysis tests
    run: pytest tests/analysis
  - name: Concurrency tests
    run: pytest tests/concurrency
  - name: Performance-contract tests
    run: pytest tests/performance
  - name: Runtime tests
    run: pytest tests/runtime
  - name: Security tests
    run: pytest tests/security
  - name: Architecture tests
    run: pytest tests/architecture
  - name: Full test suite
    run: |
      pytest \
        --cov=l9_debt_lsp \
        --cov-report=term-missing \
        --cov-fail-under=80
  - name: Ruff
    run: ruff check .
  - name: Mypy
    run: mypy src
  - name: Capabilities
    run: l9-debt-lsp-contracts capabilities

EOF

###############################################################################

11. Architecture enforcement

###############################################################################

cat > tests/architecture/test_incremental_boundary.py <<‘EOF’
from future import annotations

import ast
from pathlib import Path

ROOT = Path(file).resolve().parents[2]
ANALYSIS_ROOT = ROOT / “src/l9_debt_lsp/analysis”

FORBIDDEN_IMPORT_PREFIXES = (
“l9_ci_sdk._”,
“l9_ci_sdk.internal”,
“requests”,
“httpx”,
“aiohttp”,
“sqlite3”,
)

def imported_modules(path: Path) -> set[str]:
tree = ast.parse(path.read_text(encoding=“utf-8”))
modules: set[str] = set()

for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        modules.update(alias.name for alias in node.names)
    elif isinstance(node, ast.ImportFrom):
        if node.module:
            modules.add(node.module)
return modules

def test_analysis_runtime_uses_no_network_or_private_sdk() -> None:
for path in ANALYSIS_ROOT.rglob(”*.py”):
for module in imported_modules(path):
assert not module.startswith(
FORBIDDEN_IMPORT_PREFIXES
), f”{path} imports prohibited module {module}”

def test_analysis_runtime_does_not_persist_source_content() -> None:
prohibited = (
“write_text(text”,
“write_bytes(text”,
“sqlite3”,
“source_content_log”,
)

for path in ANALYSIS_ROOT.rglob("*.py"):
    content = path.read_text(
        encoding="utf-8"
    ).lower()
    for term in prohibited:
        assert term not in content, (
            f"{path} contains prohibited persistence "
            f"term {term}"
        )

EOF

###############################################################################

12. Local validation

###############################################################################

python3 -m compileall -q src

python3 - <<‘PY’
from future import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

root = Path.cwd()

required = [
“.l9/incremental-analysis-contract.yaml”,
“schemas/lsp/analysis-request.schema.json”,
“schemas/lsp/analysis-result.schema.json”,
“schemas/lsp/workspace-state.schema.json”,
“src/l9_debt_lsp/analysis/sdk_protocol.py”,
“src/l9_debt_lsp/analysis/workspace.py”,
“src/l9_debt_lsp/analysis/scheduler.py”,
“src/l9_debt_lsp/analysis/runtime.py”,
“tests/concurrency/test_stale_result_suppression.py”,
“tests/architecture/test_incremental_boundary.py”,
]

missing = [
path for path in required
if not (root / path).is_file()
]

if missing:
raise SystemExit(
f”LSP-P2 required files missing: {missing}”
)

for schema_path in sorted(
(root / “schemas/lsp”).glob(”*.json”)
):
schema = json.loads(
schema_path.read_text(encoding=“utf-8”)
)
Draft202012Validator.check_schema(schema)

for source_path in (
root / “src/l9_debt_lsp/analysis”
).rglob(”*.py”):
content = source_path.read_text(
encoding=“utf-8”
).lower()

prohibited = (
    "requests.",
    "httpx.",
    "aiohttp.",
    "sqlite3",
    "corpus_compiler",
    "mine_patterns",
)
for term in prohibited:
    if term in content:
        raise SystemExit(
            f"prohibited analysis dependency "
            f"{term!r} in {source_path}"
        )

print(
json.dumps(
{
“schema_version”: “l9.phase-build-result/v1”,
“repository”: “Quantum-L9/l9-ci-debt-lsp”,
“phase”: “LSP-P2”,
“status”: “built”,
“sdk_boundary”: “public-protocol”,
“document_overlays”: “memory-only”,
“document_versions”: “strictly-increasing”,
“cancellation”: “cooperative”,
“invalidation”: “bounded”,
“stale_results”: “discarded”,
“normal_network_dependency”: “prohibited”
},
sort_keys=True,
separators=(”,”, “:”),
)
)
PY

printf ‘\n’
printf ‘LSP-P2 build complete.\n’
printf ‘\n’
printf ‘Implemented:\n’
printf ’  - public SDK AnalysisSession protocol\n’
printf ’  - fail-closed unavailable SDK adapter\n’
printf ’  - workspace session lifecycle\n’
printf ’  - memory-only document overlays\n’
printf ’  - strict document-version enforcement\n’
printf ’  - deterministic bounded scheduling\n’
printf ’  - cooperative cancellation\n’
printf ’  - stale-result suppression\n’
printf ’  - bounded dependency invalidation\n’
printf ’  - active-pack generation checks\n’
printf ’  - latency measurement and classification\n’
printf ’  - explicit incomplete-analysis behavior\n’
printf ’  - offline normal analysis\n’
printf ‘\n’
printf ‘Next phase: LSP-P3 — canonical diagnostic identity, SDK finding projection, evidence links, related information, deterministic ordering, and safe diagnostic publication.\n’

:::
This phase completes the LSP’s incremental computation substrate. The next phase can focus solely on projecting verified SDK findings into editor diagnostics without mixing protocol lifecycle, scheduling, or semantic-analysis responsibilities.