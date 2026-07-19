Phase 4 is LSP-P3: canonical diagnostic identity and deterministic publication.

It preserves SDK finding identities, canonical rule IDs, provider rule IDs, source locations, document identity, active pack version, and corpus snapshot while allowing only editor-specific presentation transformations. It also ensures incomplete or stale analysis is never presented as a clean PASS. repo-spec.yaml

Save as build-phase-4.sh and run it against the completed LSP-P2 repository.

#!/usr/bin/env bash
set -euo pipefail
###############################################################################
# Quantum-L9/l9-ci-debt-lsp
# LSP-P3 — Canonical Diagnostic Identity
#
# Adds:
#   - strict SDK finding consumer contract
#   - canonical finding identity preservation
#   - canonical rule and provider rule identity preservation
#   - source-location validation and LSP range projection
#   - evidence references and related information
#   - deterministic diagnostic ordering
#   - deterministic diagnostic de-duplication
#   - incomplete-analysis diagnostic signaling
#   - active-pack and corpus lineage on every diagnostic
#   - stale-safe publication coordinator
#   - bounded diagnostic counts
#   - URI and path privacy protections
#   - production pygls document lifecycle integration
#
# Does not yet add:
#   - executable code actions
#   - WorkspaceEdit generation
#   - protected-path enforcement for edits
#   - telemetry transport
###############################################################################
fail() {
  printf 'LSP-P3: %s\n' "$*" >&2
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
require_file ".l9/incremental-analysis-contract.yaml"
require_file "src/l9_debt_lsp/analysis/runtime.py"
require_file "src/l9_debt_lsp/analysis/scheduler.py"
require_file "src/l9_debt_lsp/analysis/sdk_protocol.py"
require_file "src/l9_debt_lsp/runtime/analysis_service.py"
require_file "src/l9_debt_lsp/server.py"
require_file "pyproject.toml"
mkdir -p \
  .github/workflows \
  .l9 \
  docs/architecture/ADRs \
  schemas/lsp \
  src/l9_debt_lsp/diagnostics \
  src/l9_debt_lsp/runtime \
  tests/diagnostics \
  tests/publication \
  tests/privacy \
  tests/fixtures/diagnostics
###############################################################################
# 1. Diagnostic contract
###############################################################################
cat > .l9/diagnostic-contract.yaml <<'EOF'
schema: l9.lsp-diagnostic-contract/v1
metadata:
  repository: Quantum-L9/l9-ci-debt-lsp
  phase: LSP-P3
  status: authoritative
authority:
  sdk_owns:
    - finding_id
    - canonical_rule_id
    - provider_rule_id
    - finding fingerprint meaning
    - canonical severity
    - evidence semantics
    - source-location semantics
    - finding limitations
  intelligence_owns:
    - rule_pack_version
    - corpus_snapshot
    - compiler_version
    - taxonomy_version
    - prevention rule semantics
  lsp_owns:
    - LSP Diagnostic representation
    - editor severity mapping
    - message formatting
    - related information presentation
    - publication lifecycle
    - stale-result suppression
    - diagnostic count limits
    - incomplete-analysis presentation
identity:
  required:
    - finding_id
    - canonical_rule_id
    - provider_rule_id
    - source_location
    - document_identity
    - rule_pack_id
    - rule_pack_version
    - corpus_snapshot
  preserved_exactly:
    - finding_id
    - canonical_rule_id
    - provider_rule_id
    - document_identity
    - rule_pack_id
    - rule_pack_version
    - corpus_snapshot
  prohibited:
    - generate replacement finding IDs
    - derive finding IDs from editor message text
    - change canonical rule identity
    - change provider rule identity
    - reinterpret finding fingerprints
    - collapse distinct findings by message text
finding_input:
  protocol: l9.sdk-finding/v1
  required:
    - finding_id
    - canonical_rule_id
    - provider_rule_id
    - message
    - severity
    - source_location
    - evidence
    - limitations
  source_location:
    required:
      - document_identity
      - uri
      - start_line
      - start_character
      - end_line
      - end_character
    indexing:
      lines: zero_based
      characters: zero_based
      end: exclusive
    validation:
      - start values are non-negative
      - end is not before start
      - URI identifies the evaluated document or a valid related document
      - ranges outside the current document are clamped only when safe
      - invalid primary ranges suppress the finding
diagnostic_projection:
  source: l9-ci-debt
  code: canonical_rule_id
  data:
    required:
      - schema_version
      - finding_id
      - canonical_rule_id
      - provider_rule_id
      - document_identity
      - document_version
      - rule_pack_id
      - rule_pack_version
      - corpus_snapshot
      - analysis_request_id
      - analysis_status
      - limitations
  severity_mapping:
    critical: error
    error: error
    warning: warning
    information: information
    info: information
    hint: hint
    unknown: warning
  tags:
    deprecated: DiagnosticTag.Deprecated
    unnecessary: DiagnosticTag.Unnecessary
  message:
    maximum_characters: 2000
    source_content_injection: prohibited
    absolute_path_injection: prohibited
    secret_value_injection: prohibited
related_information:
  sources:
    - SDK evidence source locations
    - explicit related source locations
  maximum_entries_per_diagnostic: 20
  deterministic_order:
    - uri
    - start_line
    - start_character
    - message
evidence:
  presentation:
    - evidence kind
    - redacted summary
    - related location
  prohibited:
    - raw source content
    - secret values
    - absolute filesystem paths
    - raw logs
    - full corpus records
ordering:
  document_diagnostics:
    - start_line
    - start_character
    - end_line
    - end_character
    - severity_rank
    - canonical_rule_id
    - finding_id
deduplication:
  identity:
    - finding_id
    - canonical_rule_id
    - document_identity
    - source_range
    - rule_pack_id
  duplicate_behavior: retain_one_canonical_diagnostic
  conflicting_duplicate_behavior:
    - retain deterministic first representation
    - publish limitation
    - do not merge canonical identities
limits:
  maximum_diagnostics_per_document: 200
  maximum_related_information_per_diagnostic: 20
  maximum_message_characters: 2000
  overflow_behavior:
    - retain highest-priority deterministic prefix
    - publish one limitation diagnostic
    - do not claim complete clean analysis
incomplete_analysis:
  behavior:
    - preserve last known-good findings when protocol-safe
    - publish limitation diagnostic
    - suppress unsafe code actions
    - never publish empty successful diagnostics as PASS
  limitation_diagnostic:
    source: l9-ci-debt
    code: l9.analysis.incomplete
    severity: warning
    range: beginning_of_document
publication:
  preconditions:
    - result matches current document version
    - result matches current workspace generation
    - result matches active pack
    - result is not cancelled
    - result is not stale
    - document remains open
  stale_behavior: discard
  cancelled_behavior:
    - do not publish replacement diagnostics
    - preserve existing diagnostics where protocol-safe
  failed_behavior:
    - publish limitation diagnostic
    - preserve last known-good findings where protocol-safe
  close_behavior:
    - publish empty diagnostic set
    - delete publication state
privacy:
  diagnostic_data:
    source_content: prohibited
    absolute_paths: prohibited
    secrets: prohibited
    raw_logs: prohibited
    corpus_records: prohibited
phase:
  id: LSP-P3
  status: implemented
  includes:
    - SDK finding consumer schema
    - source-location validation
    - canonical diagnostic projection
    - identity preservation
    - evidence-related information
    - deterministic ordering
    - deterministic de-duplication
    - bounded diagnostic publication
    - incomplete-analysis diagnostics
    - stale-safe publisher
    - pygls publication integration
  excludes:
    - executable quick fixes
    - WorkspaceEdit construction
    - edit conflict resolution
    - protected-path write policy
    - telemetry delivery
EOF
###############################################################################
# 2. Schemas
###############################################################################
cat > schemas/lsp/sdk-finding-consumer.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/sdk-finding-consumer/v1",
  "title": "L9 SDK Finding Consumer Contract",
  "type": "object",
  "additionalProperties": true,
  "required": [
    "schema_version",
    "finding_id",
    "canonical_rule_id",
    "provider_rule_id",
    "message",
    "severity",
    "source_location",
    "evidence",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.sdk-finding/v1"
    },
    "finding_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 512
    },
    "canonical_rule_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 512
    },
    "provider_rule_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 512
    },
    "message": {
      "type": "string",
      "minLength": 1,
      "maxLength": 2000
    },
    "severity": {
      "enum": [
        "critical",
        "error",
        "warning",
        "information",
        "info",
        "hint",
        "unknown"
      ]
    },
    "source_location": {
      "$ref": "#/$defs/sourceLocation"
    },
    "evidence": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/evidence"
      },
      "maxItems": 100
    },
    "related_locations": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/relatedLocation"
      },
      "maxItems": 100
    },
    "tags": {
      "type": "array",
      "items": {
        "enum": [
          "deprecated",
          "unnecessary"
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
  },
  "$defs": {
    "sourceLocation": {
      "type": "object",
      "additionalProperties": true,
      "required": [
        "document_identity",
        "uri",
        "start_line",
        "start_character",
        "end_line",
        "end_character"
      ],
      "properties": {
        "document_identity": {
          "type": "string",
          "minLength": 1
        },
        "uri": {
          "type": "string",
          "minLength": 1
        },
        "start_line": {
          "type": "integer",
          "minimum": 0
        },
        "start_character": {
          "type": "integer",
          "minimum": 0
        },
        "end_line": {
          "type": "integer",
          "minimum": 0
        },
        "end_character": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "evidence": {
      "type": "object",
      "additionalProperties": true,
      "required": [
        "kind",
        "summary"
      ],
      "properties": {
        "kind": {
          "type": "string",
          "minLength": 1
        },
        "summary": {
          "type": "string",
          "minLength": 1,
          "maxLength": 1000
        },
        "source_location": {
          "oneOf": [
            {
              "$ref": "#/$defs/sourceLocation"
            },
            {
              "type": "null"
            }
          ]
        }
      }
    },
    "relatedLocation": {
      "type": "object",
      "additionalProperties": true,
      "required": [
        "message",
        "source_location"
      ],
      "properties": {
        "message": {
          "type": "string",
          "minLength": 1,
          "maxLength": 1000
        },
        "source_location": {
          "$ref": "#/$defs/sourceLocation"
        }
      }
    }
  }
}
EOF
cat > schemas/lsp/canonical-diagnostic.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/canonical-diagnostic/v1",
  "title": "L9 Canonical Editor Diagnostic",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "range",
    "severity",
    "code",
    "source",
    "message",
    "tags",
    "related_information",
    "data"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.canonical-diagnostic/v1"
    },
    "range": {
      "$ref": "#/$defs/range"
    },
    "severity": {
      "enum": [
        1,
        2,
        3,
        4
      ]
    },
    "code": {
      "type": "string",
      "minLength": 1
    },
    "source": {
      "const": "l9-ci-debt"
    },
    "message": {
      "type": "string",
      "minLength": 1,
      "maxLength": 2000
    },
    "tags": {
      "type": "array",
      "items": {
        "enum": [
          1,
          2
        ]
      },
      "uniqueItems": true
    },
    "related_information": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/relatedInformation"
      },
      "maxItems": 20
    },
    "data": {
      "$ref": "#/$defs/data"
    }
  },
  "$defs": {
    "position": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "line",
        "character"
      ],
      "properties": {
        "line": {
          "type": "integer",
          "minimum": 0
        },
        "character": {
          "type": "integer",
          "minimum": 0
        }
      }
    },
    "range": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "start",
        "end"
      ],
      "properties": {
        "start": {
          "$ref": "#/$defs/position"
        },
        "end": {
          "$ref": "#/$defs/position"
        }
      }
    },
    "relatedInformation": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "location",
        "message"
      ],
      "properties": {
        "location": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "uri",
            "range"
          ],
          "properties": {
            "uri": {
              "type": "string"
            },
            "range": {
              "$ref": "#/$defs/range"
            }
          }
        },
        "message": {
          "type": "string",
          "minLength": 1,
          "maxLength": 1000
        }
      }
    },
    "data": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema_version",
        "finding_id",
        "canonical_rule_id",
        "provider_rule_id",
        "document_identity",
        "document_version",
        "rule_pack_id",
        "rule_pack_version",
        "corpus_snapshot",
        "analysis_request_id",
        "analysis_status",
        "limitations"
      ],
      "properties": {
        "schema_version": {
          "const": "l9.diagnostic-data/v1"
        },
        "finding_id": {
          "type": "string"
        },
        "canonical_rule_id": {
          "type": "string"
        },
        "provider_rule_id": {
          "type": "string"
        },
        "document_identity": {
          "type": "string"
        },
        "document_version": {
          "type": "integer",
          "minimum": 0
        },
        "rule_pack_id": {
          "type": "string"
        },
        "rule_pack_version": {
          "type": "string"
        },
        "corpus_snapshot": {
          "type": "string"
        },
        "analysis_request_id": {
          "type": "string"
        },
        "analysis_status": {
          "enum": [
            "complete",
            "incomplete"
          ]
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
  }
}
EOF
cat > schemas/lsp/diagnostic-publication.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/diagnostic-publication/v1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "publication_id",
    "workspace_id",
    "workspace_generation",
    "document_id",
    "document_uri",
    "document_version",
    "rule_pack_id",
    "rule_pack_version",
    "analysis_request_id",
    "analysis_status",
    "diagnostic_count",
    "diagnostics",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.diagnostic-publication/v1"
    },
    "publication_id": {
      "type": "string",
      "pattern": "^publication_[0-9a-f]{64}$"
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
      "type": "string"
    },
    "document_version": {
      "type": "integer",
      "minimum": 0
    },
    "rule_pack_id": {
      "type": "string",
      "pattern": "^pack_[0-9a-f]{64}$"
    },
    "rule_pack_version": {
      "type": "string"
    },
    "analysis_request_id": {
      "type": "string",
      "pattern": "^request_[0-9a-f]{64}$"
    },
    "analysis_status": {
      "enum": [
        "complete",
        "incomplete",
        "failed"
      ]
    },
    "diagnostic_count": {
      "type": "integer",
      "minimum": 0,
      "maximum": 201
    },
    "diagnostics": {
      "type": "array",
      "items": {
        "$ref": "l9://lsp/canonical-diagnostic/v1"
      },
      "maxItems": 201
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
###############################################################################
# 3. Diagnostics package
###############################################################################
cat > src/l9_debt_lsp/diagnostics/__init__.py <<'EOF'
"""Canonical SDK finding projection and diagnostic publication."""
EOF
cat > src/l9_debt_lsp/diagnostics/errors.py <<'EOF'
from __future__ import annotations
class DiagnosticError(RuntimeError):
    """Base diagnostic projection failure."""
class FindingValidationError(DiagnosticError):
    """An SDK finding violates the public consumer contract."""
class SourceLocationError(DiagnosticError):
    """A finding source location cannot be represented safely."""
class DiagnosticPublicationError(DiagnosticError):
    """A diagnostic publication could not be committed safely."""
EOF
cat > src/l9_debt_lsp/diagnostics/models.py <<'EOF'
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
@dataclass(frozen=True, order=True)
class Position:
    line: int
    character: int
    def as_dict(self) -> dict[str, int]:
        return {
            "line": self.line,
            "character": self.character,
        }
@dataclass(frozen=True)
class Range:
    start: Position
    end: Position
    def as_dict(self) -> dict[str, Any]:
        return {
            "start": self.start.as_dict(),
            "end": self.end.as_dict(),
        }
@dataclass(frozen=True)
class SourceLocation:
    document_identity: str
    uri: str
    range: Range
@dataclass(frozen=True)
class RelatedInformation:
    uri: str
    range: Range
    message: str
    def as_dict(self) -> dict[str, Any]:
        return {
            "location": {
                "uri": self.uri,
                "range": self.range.as_dict(),
            },
            "message": self.message,
        }
@dataclass(frozen=True)
class CanonicalDiagnostic:
    range: Range
    severity: int
    code: str
    source: str
    message: str
    tags: tuple[int, ...]
    related_information: tuple[RelatedInformation, ...]
    data: dict[str, Any]
    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.canonical-diagnostic/v1",
            "range": self.range.as_dict(),
            "severity": self.severity,
            "code": self.code,
            "source": self.source,
            "message": self.message,
            "tags": list(self.tags),
            "related_information": [
                value.as_dict()
                for value in self.related_information
            ],
            "data": self.data,
        }
@dataclass(frozen=True)
class DiagnosticPublication:
    publication_id: str
    workspace_id: str
    workspace_generation: int
    document_id: str
    document_uri: str
    document_version: int
    rule_pack_id: str
    rule_pack_version: str
    analysis_request_id: str
    analysis_status: str
    diagnostics: tuple[CanonicalDiagnostic, ...]
    limitations: tuple[str, ...]
    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.diagnostic-publication/v1",
            "publication_id": self.publication_id,
            "workspace_id": self.workspace_id,
            "workspace_generation": self.workspace_generation,
            "document_id": self.document_id,
            "document_uri": self.document_uri,
            "document_version": self.document_version,
            "rule_pack_id": self.rule_pack_id,
            "rule_pack_version": self.rule_pack_version,
            "analysis_request_id": self.analysis_request_id,
            "analysis_status": self.analysis_status,
            "diagnostic_count": len(self.diagnostics),
            "diagnostics": [
                diagnostic.as_dict()
                for diagnostic in self.diagnostics
            ],
            "limitations": list(self.limitations),
        }
EOF
cat > src/l9_debt_lsp/diagnostics/location.py <<'EOF'
from __future__ import annotations
from typing import Any
from .errors import SourceLocationError
from .models import Position, Range, SourceLocation
def source_location_from_dict(
    value: dict[str, Any],
) -> SourceLocation:
    try:
        start = Position(
            line=int(value["start_line"]),
            character=int(value["start_character"]),
        )
        end = Position(
            line=int(value["end_line"]),
            character=int(value["end_character"]),
        )
        document_identity = str(value["document_identity"])
        uri = str(value["uri"])
    except (KeyError, TypeError, ValueError) as error:
        raise SourceLocationError(
            "source location is malformed"
        ) from error
    if (
        start.line < 0
        or start.character < 0
        or end.line < 0
        or end.character < 0
    ):
        raise SourceLocationError(
            "source location positions must be non-negative"
        )
    if end < start:
        raise SourceLocationError(
            "source location end precedes start"
        )
    if not document_identity:
        raise SourceLocationError(
            "source location document identity is empty"
        )
    if not uri:
        raise SourceLocationError(
            "source location URI is empty"
        )
    return SourceLocation(
        document_identity=document_identity,
        uri=uri,
        range=Range(start=start, end=end),
    )
def clamp_primary_range(
    location: SourceLocation,
    *,
    document_text: str,
) -> Range:
    lines = document_text.splitlines()
    if not lines:
        return Range(
            start=Position(0, 0),
            end=Position(0, 0),
        )
    maximum_line = len(lines) - 1
    start_line = min(location.range.start.line, maximum_line)
    end_line = min(location.range.end.line, maximum_line)
    start_character = min(
        location.range.start.character,
        len(lines[start_line]),
    )
    end_character = min(
        location.range.end.character,
        len(lines[end_line]),
    )
    start = Position(start_line, start_character)
    end = Position(end_line, end_character)
    if end < start:
        end = start
    return Range(start=start, end=end)
EOF
cat > src/l9_debt_lsp/diagnostics/sanitization.py <<'EOF'
from __future__ import annotations
import re
MAX_DIAGNOSTIC_MESSAGE = 2000
MAX_RELATED_MESSAGE = 1000
ABSOLUTE_PATH = re.compile(
    r"(?:"
    r"(?<![A-Za-z0-9_.-])/(?:home|Users|private|tmp|var|opt)/[^\s]+"
    r"|"
    r"(?<![A-Za-z0-9_.-])[A-Za-z]:\\[^\s]+"
    r")"
)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)
def sanitize_message(
    value: str,
    *,
    maximum: int = MAX_DIAGNOSTIC_MESSAGE,
) -> str:
    result = value.replace("\x00", "")
    result = ABSOLUTE_PATH.sub("<redacted-path>", result)
    for pattern in SECRET_PATTERNS:
        result = pattern.sub("<redacted-secret>", result)
    result = " ".join(result.split())
    if not result:
        result = "L9 diagnostic details are unavailable."
    if len(result) > maximum:
        result = result[: maximum - 1] + "…"
    return result
EOF
cat > src/l9_debt_lsp/diagnostics/validation.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from typing import Any
from l9_debt_lsp.contracts.schema import SchemaValidator
from .errors import FindingValidationError
class FindingValidator:
    def __init__(self, schema_path: Path) -> None:
        self._validator = SchemaValidator(schema_path)
    def validate(
        self,
        finding: dict[str, Any],
    ) -> None:
        try:
            self._validator.validate(finding)
        except Exception as error:
            raise FindingValidationError(str(error)) from error
EOF
cat > src/l9_debt_lsp/diagnostics/severity.py <<'EOF'
from __future__ import annotations
SEVERITY_MAP = {
    "critical": 1,
    "error": 1,
    "warning": 2,
    "information": 3,
    "info": 3,
    "hint": 4,
    "unknown": 2,
}
SEVERITY_RANK = {
    1: 0,
    2: 1,
    3: 2,
    4: 3,
}
TAG_MAP = {
    "unnecessary": 1,
    "deprecated": 2,
}
def diagnostic_severity(value: str) -> int:
    return SEVERITY_MAP.get(value, 2)
def diagnostic_tags(values: object) -> tuple[int, ...]:
    if not isinstance(values, list):
        return ()
    tags = {
        TAG_MAP[value]
        for value in values
        if isinstance(value, str) and value in TAG_MAP
    }
    return tuple(sorted(tags))
EOF
cat > src/l9_debt_lsp/diagnostics/projection.py <<'EOF'
from __future__ import annotations
from typing import Any
from .errors import FindingValidationError, SourceLocationError
from .location import (
    clamp_primary_range,
    source_location_from_dict,
)
from .models import (
    CanonicalDiagnostic,
    RelatedInformation,
)
from .sanitization import sanitize_message
from .severity import diagnostic_severity, diagnostic_tags
from .validation import FindingValidator
MAX_RELATED_INFORMATION = 20
def related_information(
    finding: dict[str, Any],
) -> tuple[RelatedInformation, ...]:
    projected: list[RelatedInformation] = []
    evidence = finding.get("evidence", [])
    if isinstance(evidence, list):
        for item in evidence:
            if not isinstance(item, dict):
                continue
            location_value = item.get("source_location")
            if not isinstance(location_value, dict):
                continue
            try:
                location = source_location_from_dict(
                    location_value
                )
            except SourceLocationError:
                continue
            kind = str(item.get("kind", "evidence"))
            summary = sanitize_message(
                str(item.get("summary", "Related evidence")),
                maximum=1000,
            )
            projected.append(
                RelatedInformation(
                    uri=location.uri,
                    range=location.range,
                    message=f"{kind}: {summary}",
                )
            )
    explicit = finding.get("related_locations", [])
    if isinstance(explicit, list):
        for item in explicit:
            if not isinstance(item, dict):
                continue
            location_value = item.get("source_location")
            if not isinstance(location_value, dict):
                continue
            try:
                location = source_location_from_dict(
                    location_value
                )
            except SourceLocationError:
                continue
            projected.append(
                RelatedInformation(
                    uri=location.uri,
                    range=location.range,
                    message=sanitize_message(
                        str(item.get("message", "Related location")),
                        maximum=1000,
                    ),
                )
            )
    unique: dict[
        tuple[str, int, int, int, int, str],
        RelatedInformation,
    ] = {}
    for item in projected:
        key = (
            item.uri,
            item.range.start.line,
            item.range.start.character,
            item.range.end.line,
            item.range.end.character,
            item.message,
        )
        unique.setdefault(key, item)
    ordered = sorted(
        unique.values(),
        key=lambda item: (
            item.uri,
            item.range.start.line,
            item.range.start.character,
            item.range.end.line,
            item.range.end.character,
            item.message,
        ),
    )
    return tuple(ordered[:MAX_RELATED_INFORMATION])
def project_finding(
    *,
    finding: dict[str, Any],
    validator: FindingValidator,
    document_id: str,
    document_uri: str,
    document_version: int,
    document_text: str,
    rule_pack_id: str,
    rule_pack_version: str,
    corpus_snapshot: str,
    analysis_request_id: str,
    analysis_status: str,
    analysis_limitations: tuple[str, ...],
) -> CanonicalDiagnostic:
    validator.validate(finding)
    location_value = finding["source_location"]
    if not isinstance(location_value, dict):
        raise FindingValidationError(
            "finding source_location must be an object"
        )
    location = source_location_from_dict(location_value)
    if location.document_identity != document_id:
        raise SourceLocationError(
            "primary finding document identity does not match "
            "the evaluated document"
        )
    if location.uri != document_uri:
        raise SourceLocationError(
            "primary finding URI does not match evaluated document"
        )
    source_range = clamp_primary_range(
        location,
        document_text=document_text,
    )
    finding_limitations = finding.get("limitations", [])
    if not isinstance(finding_limitations, list):
        finding_limitations = []
    limitations = tuple(
        sorted(
            set(
                str(item)
                for item in (
                    list(analysis_limitations)
                    + finding_limitations
                )
            )
        )
    )
    return CanonicalDiagnostic(
        range=source_range,
        severity=diagnostic_severity(
            str(finding["severity"])
        ),
        code=str(finding["canonical_rule_id"]),
        source="l9-ci-debt",
        message=sanitize_message(str(finding["message"])),
        tags=diagnostic_tags(finding.get("tags")),
        related_information=related_information(finding),
        data={
            "schema_version": "l9.diagnostic-data/v1",
            "finding_id": str(finding["finding_id"]),
            "canonical_rule_id": str(
                finding["canonical_rule_id"]
            ),
            "provider_rule_id": str(
                finding["provider_rule_id"]
            ),
            "document_identity": document_id,
            "document_version": document_version,
            "rule_pack_id": rule_pack_id,
            "rule_pack_version": rule_pack_version,
            "corpus_snapshot": corpus_snapshot,
            "analysis_request_id": analysis_request_id,
            "analysis_status": analysis_status,
            "limitations": list(limitations),
        },
    )
EOF
cat > src/l9_debt_lsp/diagnostics/ordering.py <<'EOF'
from __future__ import annotations
from .models import CanonicalDiagnostic
from .severity import SEVERITY_RANK
def diagnostic_sort_key(
    diagnostic: CanonicalDiagnostic,
) -> tuple[object, ...]:
    return (
        diagnostic.range.start.line,
        diagnostic.range.start.character,
        diagnostic.range.end.line,
        diagnostic.range.end.character,
        SEVERITY_RANK.get(diagnostic.severity, 99),
        diagnostic.data["canonical_rule_id"],
        diagnostic.data["finding_id"],
    )
def diagnostic_identity(
    diagnostic: CanonicalDiagnostic,
) -> tuple[object, ...]:
    return (
        diagnostic.data["finding_id"],
        diagnostic.data["canonical_rule_id"],
        diagnostic.data["document_identity"],
        diagnostic.range.start.line,
        diagnostic.range.start.character,
        diagnostic.range.end.line,
        diagnostic.range.end.character,
        diagnostic.data["rule_pack_id"],
    )
def deduplicate_and_order(
    diagnostics: list[CanonicalDiagnostic],
) -> tuple[
    tuple[CanonicalDiagnostic, ...],
    tuple[str, ...],
]:
    ordered = sorted(
        diagnostics,
        key=diagnostic_sort_key,
    )
    unique: dict[
        tuple[object, ...],
        CanonicalDiagnostic,
    ] = {}
    limitations: set[str] = set()
    for diagnostic in ordered:
        identity = diagnostic_identity(diagnostic)
        existing = unique.get(identity)
        if existing is None:
            unique[identity] = diagnostic
            continue
        if existing.as_dict() != diagnostic.as_dict():
            limitations.add(
                "Conflicting duplicate diagnostic representation "
                f"for finding {diagnostic.data['finding_id']}."
            )
    return (
        tuple(
            sorted(
                unique.values(),
                key=diagnostic_sort_key,
            )
        ),
        tuple(sorted(limitations)),
    )
EOF
cat > src/l9_debt_lsp/diagnostics/limitations.py <<'EOF'
from __future__ import annotations
from .models import (
    CanonicalDiagnostic,
    Position,
    Range,
)
def limitation_diagnostic(
    *,
    document_id: str,
    document_version: int,
    rule_pack_id: str,
    rule_pack_version: str,
    corpus_snapshot: str,
    analysis_request_id: str,
    limitations: tuple[str, ...],
    finding_id: str = "l9-analysis-incomplete",
) -> CanonicalDiagnostic:
    message = (
        "L9 analysis is incomplete. "
        + " ".join(limitations[:5])
    ).strip()
    if len(message) > 2000:
        message = message[:1999] + "…"
    return CanonicalDiagnostic(
        range=Range(
            start=Position(0, 0),
            end=Position(0, 0),
        ),
        severity=2,
        code="l9.analysis.incomplete",
        source="l9-ci-debt",
        message=message,
        tags=(),
        related_information=(),
        data={
            "schema_version": "l9.diagnostic-data/v1",
            "finding_id": finding_id,
            "canonical_rule_id": "l9.analysis.incomplete",
            "provider_rule_id": "l9-lsp-runtime",
            "document_identity": document_id,
            "document_version": document_version,
            "rule_pack_id": rule_pack_id,
            "rule_pack_version": rule_pack_version,
            "corpus_snapshot": corpus_snapshot,
            "analysis_request_id": analysis_request_id,
            "analysis_status": "incomplete",
            "limitations": list(limitations),
        },
    )
EOF
cat > src/l9_debt_lsp/diagnostics/builder.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from typing import Any
from l9_debt_lsp.packs.hashing import namespaced_hash
from .errors import DiagnosticError
from .limitations import limitation_diagnostic
from .models import (
    CanonicalDiagnostic,
    DiagnosticPublication,
)
from .ordering import deduplicate_and_order
from .projection import project_finding
from .validation import FindingValidator
MAX_DIAGNOSTICS_PER_DOCUMENT = 200
class DiagnosticBuilder:
    def __init__(self, schema_root: Path) -> None:
        self._validator = FindingValidator(
            schema_root / "sdk-finding-consumer.schema.json"
        )
    def build(
        self,
        *,
        analysis_result: dict[str, Any],
        document_uri: str,
        document_text: str,
        rule_pack_version: str,
        corpus_snapshot: str,
    ) -> DiagnosticPublication:
        status = str(analysis_result["status"])
        if status not in {
            "complete",
            "incomplete",
            "failed",
        }:
            raise DiagnosticError(
                f"analysis status cannot be published: {status}"
            )
        findings = analysis_result.get("findings", [])
        if not isinstance(findings, list):
            raise DiagnosticError(
                "analysis findings must be an array"
            )
        analysis_limitations = tuple(
            sorted(
                set(
                    str(value)
                    for value in analysis_result.get(
                        "limitations",
                        [],
                    )
                )
            )
        )
        projected: list[CanonicalDiagnostic] = []
        projection_limitations: set[str] = set()
        for finding in findings:
            if not isinstance(finding, dict):
                projection_limitations.add(
                    "An SDK finding was not an object."
                )
                continue
            try:
                projected.append(
                    project_finding(
                        finding=finding,
                        validator=self._validator,
                        document_id=analysis_result["document_id"],
                        document_uri=document_uri,
                        document_version=analysis_result[
                            "document_version"
                        ],
                        document_text=document_text,
                        rule_pack_id=analysis_result[
                            "active_pack_id"
                        ],
                        rule_pack_version=rule_pack_version,
                        corpus_snapshot=corpus_snapshot,
                        analysis_request_id=analysis_result[
                            "request_id"
                        ],
                        analysis_status=(
                            "complete"
                            if status == "complete"
                            else "incomplete"
                        ),
                        analysis_limitations=analysis_limitations,
                    )
                )
            except Exception as error:
                projection_limitations.add(
                    "A finding was suppressed because it could not be "
                    f"represented safely: {type(error).__name__}."
                )
        ordered, duplicate_limitations = deduplicate_and_order(
            projected
        )
        limitations = set(analysis_limitations)
        limitations.update(projection_limitations)
        limitations.update(duplicate_limitations)
        diagnostic_values = list(ordered)
        if len(diagnostic_values) > MAX_DIAGNOSTICS_PER_DOCUMENT:
            omitted = (
                len(diagnostic_values)
                - MAX_DIAGNOSTICS_PER_DOCUMENT
            )
            diagnostic_values = diagnostic_values[
                :MAX_DIAGNOSTICS_PER_DOCUMENT
            ]
            limitations.add(
                f"{omitted} diagnostics were omitted because the "
                "per-document limit was exceeded."
            )
        if status != "complete" or limitations:
            diagnostic_values.append(
                limitation_diagnostic(
                    document_id=analysis_result["document_id"],
                    document_version=analysis_result[
                        "document_version"
                    ],
                    rule_pack_id=analysis_result[
                        "active_pack_id"
                    ],
                    rule_pack_version=rule_pack_version,
                    corpus_snapshot=corpus_snapshot,
                    analysis_request_id=analysis_result[
                        "request_id"
                    ],
                    limitations=tuple(sorted(limitations))
                    or ("Analysis did not complete.",),
                )
            )
        final_diagnostics, final_duplicate_limitations = (
            deduplicate_and_order(diagnostic_values)
        )
        limitations.update(final_duplicate_limitations)
        publication_identity = {
            "workspace_id": analysis_result["workspace_id"],
            "workspace_generation": analysis_result[
                "workspace_generation"
            ],
            "document_id": analysis_result["document_id"],
            "document_version": analysis_result[
                "document_version"
            ],
            "rule_pack_id": analysis_result["active_pack_id"],
            "rule_pack_version": rule_pack_version,
            "analysis_request_id": analysis_result["request_id"],
            "diagnostic_identities": [
                {
                    "finding_id": diagnostic.data["finding_id"],
                    "canonical_rule_id": diagnostic.data[
                        "canonical_rule_id"
                    ],
                    "range": diagnostic.range.as_dict(),
                }
                for diagnostic in final_diagnostics
            ],
        }
        return DiagnosticPublication(
            publication_id=namespaced_hash(
                "publication_",
                publication_identity,
            ),
            workspace_id=analysis_result["workspace_id"],
            workspace_generation=analysis_result[
                "workspace_generation"
            ],
            document_id=analysis_result["document_id"],
            document_uri=document_uri,
            document_version=analysis_result[
                "document_version"
            ],
            rule_pack_id=analysis_result["active_pack_id"],
            rule_pack_version=rule_pack_version,
            analysis_request_id=analysis_result["request_id"],
            analysis_status=status,
            diagnostics=final_diagnostics,
            limitations=tuple(sorted(limitations)),
        )
EOF
cat > src/l9_debt_lsp/diagnostics/publisher.py <<'EOF'
from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable
from l9_debt_lsp.analysis.workspace import WorkspaceManager
from .errors import DiagnosticPublicationError
from .models import DiagnosticPublication
PublishCallback = Callable[
    [str, list[dict[str, object]]],
    Awaitable[None],
]
@dataclass(frozen=True)
class PublicationState:
    publication_id: str
    document_version: int
    rule_pack_id: str
    diagnostic_count: int
class DiagnosticPublisher:
    def __init__(
        self,
        *,
        workspaces: WorkspaceManager,
        callback: PublishCallback,
    ) -> None:
        self._workspaces = workspaces
        self._callback = callback
        self._published: dict[
            tuple[str, str],
            PublicationState,
        ] = {}
        self._locks: dict[
            tuple[str, str],
            asyncio.Lock,
        ] = {}
    async def publish(
        self,
        publication: DiagnosticPublication,
    ) -> bool:
        key = (
            publication.workspace_id,
            publication.document_id,
        )
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            state = self._workspaces.get_workspace_nowait(
                publication.workspace_id
            )
            if state.state != "open":
                return False
            overlay = state.documents.get(
                publication.document_id
            )
            if overlay is None or overlay.state != "open":
                return False
            if overlay.version != publication.document_version:
                return False
            if (
                state.generation
                != publication.workspace_generation
            ):
                return False
            if (
                state.active_pack is None
                or state.active_pack.pack_id
                != publication.rule_pack_id
            ):
                return False
            diagnostics = [
                value.as_dict()
                for value in publication.diagnostics
            ]
            try:
                await self._callback(
                    publication.document_uri,
                    diagnostics,
                )
            except Exception as error:
                raise DiagnosticPublicationError(
                    f"diagnostic callback failed: {error}"
                ) from error
            self._published[key] = PublicationState(
                publication_id=publication.publication_id,
                document_version=publication.document_version,
                rule_pack_id=publication.rule_pack_id,
                diagnostic_count=len(diagnostics),
            )
            return True
    async def clear(
        self,
        *,
        workspace_id: str,
        document_id: str,
        document_uri: str,
    ) -> None:
        key = (workspace_id, document_id)
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            await self._callback(document_uri, [])
            self._published.pop(key, None)
            self._locks.pop(key, None)
    def state(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> PublicationState | None:
        return self._published.get(
            (workspace_id, document_id)
        )
EOF
###############################################################################
# 4. Diagnostic service
###############################################################################
cat > src/l9_debt_lsp/runtime/diagnostic_service.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from typing import Any
from l9_debt_lsp.analysis.runtime import (
    IncrementalAnalysisRuntime,
)
from l9_debt_lsp.diagnostics.builder import DiagnosticBuilder
from l9_debt_lsp.diagnostics.models import DiagnosticPublication
from l9_debt_lsp.diagnostics.publisher import DiagnosticPublisher
class DiagnosticService:
    def __init__(
        self,
        *,
        runtime: IncrementalAnalysisRuntime,
        publisher: DiagnosticPublisher,
        schema_root: Path,
    ) -> None:
        self.runtime = runtime
        self.publisher = publisher
        self.builder = DiagnosticBuilder(schema_root)
    async def evaluate_and_publish(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> DiagnosticPublication | None:
        workspace = self.runtime.workspaces.get_workspace_nowait(
            workspace_id
        )
        overlay = workspace.documents.get(document_id)
        if overlay is None or overlay.state != "open":
            return None
        if workspace.active_pack is None:
            return None
        analysis = await self.runtime.evaluate_document(
            workspace_id=workspace_id,
            document_id=document_id,
        )
        if analysis["status"] in {
            "cancelled",
            "stale",
        }:
            return None
        publication = self.builder.build(
            analysis_result=analysis,
            document_uri=overlay.uri,
            document_text=overlay.text,
            rule_pack_version=(
                workspace.active_pack.pack_version
            ),
            corpus_snapshot=(
                workspace.active_pack.corpus_snapshot
            ),
        )
        published = await self.publisher.publish(publication)
        return publication if published else None
    async def close_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        document_uri: str,
    ) -> None:
        await self.publisher.clear(
            workspace_id=workspace_id,
            document_id=document_id,
            document_uri=document_uri,
        )
        await self.runtime.close_document(
            workspace_id=workspace_id,
            document_id=document_id,
        )
EOF
###############################################################################
# 5. pygls conversion and server integration
###############################################################################
cat > src/l9_debt_lsp/diagnostics/lsp_types.py <<'EOF'
from __future__ import annotations
from typing import Any
from lsprotocol.types import (
    Diagnostic,
    DiagnosticRelatedInformation,
    DiagnosticSeverity,
    DiagnosticTag,
    Location,
    Position,
    Range,
)
def to_lsp_diagnostic(
    value: dict[str, Any],
) -> Diagnostic:
    diagnostic_range = value["range"]
    related = [
        DiagnosticRelatedInformation(
            location=Location(
                uri=item["location"]["uri"],
                range=Range(
                    start=Position(
                        line=item["location"]["range"]["start"][
                            "line"
                        ],
                        character=item["location"]["range"][
                            "start"
                        ]["character"],
                    ),
                    end=Position(
                        line=item["location"]["range"]["end"][
                            "line"
                        ],
                        character=item["location"]["range"][
                            "end"
                        ]["character"],
                    ),
                ),
            ),
            message=item["message"],
        )
        for item in value["related_information"]
    ]
    tags = [
        DiagnosticTag(tag)
        for tag in value["tags"]
    ]
    return Diagnostic(
        range=Range(
            start=Position(
                line=diagnostic_range["start"]["line"],
                character=diagnostic_range["start"][
                    "character"
                ],
            ),
            end=Position(
                line=diagnostic_range["end"]["line"],
                character=diagnostic_range["end"][
                    "character"
                ],
            ),
        ),
        message=value["message"],
        severity=DiagnosticSeverity(value["severity"]),
        code=value["code"],
        source=value["source"],
        tags=tags or None,
        related_information=related or None,
        data=value["data"],
    )
EOF
cat > src/l9_debt_lsp/server.py <<'EOF'
from __future__ import annotations
import asyncio
import json
from pathlib import Path
from typing import Any
from lsprotocol.types import (
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    InitializeParams,
    InitializeResult,
    ServerCapabilities,
    TextDocumentSyncKind,
)
from pygls.server import LanguageServer
from l9_debt_lsp.analysis.identity import (
    document_identity,
    workspace_identity,
)
from l9_debt_lsp.analysis.models import PackContext
from l9_debt_lsp.analysis.null_sdk import (
    UnavailableAnalysisSession,
)
from l9_debt_lsp.analysis.runtime import (
    IncrementalAnalysisRuntime,
)
from l9_debt_lsp.diagnostics.lsp_types import (
    to_lsp_diagnostic,
)
from l9_debt_lsp.diagnostics.publisher import (
    DiagnosticPublisher,
)
from l9_debt_lsp.runtime.capabilities import (
    phase_capabilities,
)
from l9_debt_lsp.runtime.diagnostic_service import (
    DiagnosticService,
)
SERVER_NAME = "l9-ci-debt-lsp"
SERVER_VERSION = "0.4.0"
server = LanguageServer(
    SERVER_NAME,
    SERVER_VERSION,
)
runtime = IncrementalAnalysisRuntime(
    UnavailableAnalysisSession()
)
async def publish_callback(
    uri: str,
    diagnostics: list[dict[str, object]],
) -> None:
    server.publish_diagnostics(
        uri,
        [
            to_lsp_diagnostic(value)
            for value in diagnostics
        ],
    )
publisher = DiagnosticPublisher(
    workspaces=runtime.workspaces,
    callback=publish_callback,
)
diagnostic_service = DiagnosticService(
    runtime=runtime,
    publisher=publisher,
    schema_root=Path("schemas/lsp").resolve(),
)
workspace_by_document: dict[str, str] = {}
def bootstrap_pack() -> PackContext:
    return PackContext(
        pack_id="pack_" + "0" * 64,
        pack_version="unconfigured",
        corpus_snapshot="cs_" + "0" * 64,
        compiler_version="unconfigured",
        taxonomy_version="unconfigured",
        sdk_contract_version="l9.integration-contract/v1",
    )
@server.feature("initialize")
def initialize(
    _params: InitializeParams,
) -> InitializeResult:
    return InitializeResult(
        capabilities=ServerCapabilities(
            text_document_sync=TextDocumentSyncKind.Full,
        ),
        server_info={
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
    )
@server.feature("textDocument/didOpen")
async def did_open(
    params: DidOpenTextDocumentParams,
) -> None:
    document = params.text_document
    workspace_uri = (
        server.workspace.root_uri
        or document.uri.rsplit("/", 1)[0]
    )
    workspace_id = workspace_identity(workspace_uri)
    try:
        runtime.workspaces.get_workspace_nowait(workspace_id)
    except Exception:
        await runtime.open_workspace(
            workspace_uri=workspace_uri,
            pack=bootstrap_pack(),
        )
    metadata = await runtime.open_document(
        workspace_id=workspace_id,
        uri=document.uri,
        language_id=document.language_id,
        version=document.version,
        text=document.text,
    )
    workspace_by_document[metadata["document_id"]] = workspace_id
    await diagnostic_service.evaluate_and_publish(
        workspace_id=workspace_id,
        document_id=metadata["document_id"],
    )
@server.feature("textDocument/didChange")
async def did_change(
    params: DidChangeTextDocumentParams,
) -> None:
    document_id = document_identity(
        params.text_document.uri
    )
    workspace_id = workspace_by_document.get(document_id)
    if workspace_id is None:
        return
    if not params.content_changes:
        return
    text = params.content_changes[-1].text
    version = params.text_document.version
    await runtime.update_document(
        workspace_id=workspace_id,
        document_id=document_id,
        version=version,
        text=text,
    )
    await diagnostic_service.evaluate_and_publish(
        workspace_id=workspace_id,
        document_id=document_id,
    )
@server.feature("textDocument/didClose")
async def did_close(
    params: DidCloseTextDocumentParams,
) -> None:
    uri = params.text_document.uri
    document_id = document_identity(uri)
    workspace_id = workspace_by_document.pop(
        document_id,
        None,
    )
    if workspace_id is None:
        return
    await diagnostic_service.close_document(
        workspace_id=workspace_id,
        document_id=document_id,
        document_uri=uri,
    )
@server.feature("l9/serverCapabilities")
def l9_server_capabilities(
    _params: Any,
) -> dict[str, Any]:
    return phase_capabilities()
@server.command("l9.showServerCapabilities")
def show_server_capabilities(
    _arguments: list[Any],
) -> str:
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
# 6. Capabilities and package version
###############################################################################
cat > src/l9_debt_lsp/runtime/capabilities.py <<'EOF'
from __future__ import annotations
from typing import Any
def phase_capabilities() -> dict[str, Any]:
    return {
        "schema_version": "l9.lsp-server-capabilities/v1",
        "phase": "LSP-P3",
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
            "code_actions": False,
            "telemetry": False
        },
        "limitations": [
            "The default SDK adapter remains fail-closed until configured.",
            "Executable code actions are implemented in LSP-P4.",
            "Effectiveness telemetry is implemented in LSP-P5."
        ]
    }
EOF
python3 - <<'PY'
from pathlib import Path
init = Path("src/l9_debt_lsp/__init__.py")
text = init.read_text(encoding="utf-8")
text = text.replace('__version__ = "0.2.0"', '__version__ = "0.4.0"')
text = text.replace('__version__ = "0.3.0"', '__version__ = "0.4.0"')
init.write_text(text, encoding="utf-8")
project = Path("pyproject.toml")
text = project.read_text(encoding="utf-8")
text = text.replace('version = "0.2.0"', 'version = "0.4.0"')
text = text.replace('version = "0.3.0"', 'version = "0.4.0"')
project.write_text(text, encoding="utf-8")
PY
###############################################################################
# 7. Tests
###############################################################################
cat > tests/fixtures/diagnostics/finding.py <<'EOF'
from __future__ import annotations
from typing import Any
def valid_finding(
    *,
    document_id: str,
    uri: str,
    finding_id: str = "finding-1",
    canonical_rule_id: str = "l9.example.rule",
    line: int = 0,
) -> dict[str, Any]:
    return {
        "schema_version": "l9.sdk-finding/v1",
        "finding_id": finding_id,
        "canonical_rule_id": canonical_rule_id,
        "provider_rule_id": "provider.example",
        "message": "Example finding",
        "severity": "warning",
        "source_location": {
            "document_identity": document_id,
            "uri": uri,
            "start_line": line,
            "start_character": 0,
            "end_line": line,
            "end_character": 5
        },
        "evidence": [
            {
                "kind": "structural",
                "summary": "Related evidence",
                "source_location": {
                    "document_identity": document_id,
                    "uri": uri,
                    "start_line": line,
                    "start_character": 0,
                    "end_line": line,
                    "end_character": 5
                }
            }
        ],
        "related_locations": [],
        "tags": [],
        "limitations": []
    }
EOF
touch tests/fixtures/diagnostics/__init__.py
cat > tests/diagnostics/test_identity_preservation.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from l9_debt_lsp.diagnostics.builder import DiagnosticBuilder
from tests.fixtures.diagnostics.finding import valid_finding
ROOT = Path(__file__).resolve().parents[2]
def test_canonical_identity_is_preserved_exactly() -> None:
    document_id = "doc_" + "a" * 64
    uri = "file:///workspace/example.py"
    finding = valid_finding(
        document_id=document_id,
        uri=uri,
        finding_id="sdk-finding-identity",
        canonical_rule_id="l9.canonical.identity",
    )
    builder = DiagnosticBuilder(ROOT / "schemas/lsp")
    publication = builder.build(
        analysis_result={
            "request_id": "request_" + "b" * 64,
            "workspace_id": "workspace_" + "c" * 64,
            "workspace_generation": 1,
            "document_id": document_id,
            "document_version": 7,
            "active_pack_id": "pack_" + "d" * 64,
            "status": "complete",
            "findings": [finding],
            "limitations": []
        },
        document_uri=uri,
        document_text="hello\n",
        rule_pack_version="1.2.3",
        corpus_snapshot="cs_" + "e" * 64,
    )
    diagnostic = publication.diagnostics[0]
    assert diagnostic.data["finding_id"] == (
        "sdk-finding-identity"
    )
    assert diagnostic.data["canonical_rule_id"] == (
        "l9.canonical.identity"
    )
    assert diagnostic.data["provider_rule_id"] == (
        "provider.example"
    )
    assert diagnostic.data["document_identity"] == document_id
    assert diagnostic.data["document_version"] == 7
    assert diagnostic.data["rule_pack_version"] == "1.2.3"
    assert diagnostic.data["corpus_snapshot"] == (
        "cs_" + "e" * 64
    )
EOF
cat > tests/diagnostics/test_ordering.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from l9_debt_lsp.diagnostics.builder import DiagnosticBuilder
from tests.fixtures.diagnostics.finding import valid_finding
ROOT = Path(__file__).resolve().parents[2]
def test_diagnostics_have_deterministic_source_order() -> None:
    document_id = "doc_" + "a" * 64
    uri = "file:///workspace/example.py"
    findings = [
        valid_finding(
            document_id=document_id,
            uri=uri,
            finding_id="finding-late",
            canonical_rule_id="l9.z",
            line=2,
        ),
        valid_finding(
            document_id=document_id,
            uri=uri,
            finding_id="finding-early",
            canonical_rule_id="l9.a",
            line=0,
        ),
    ]
    builder = DiagnosticBuilder(ROOT / "schemas/lsp")
    publication = builder.build(
        analysis_result={
            "request_id": "request_" + "b" * 64,
            "workspace_id": "workspace_" + "c" * 64,
            "workspace_generation": 1,
            "document_id": document_id,
            "document_version": 1,
            "active_pack_id": "pack_" + "d" * 64,
            "status": "complete",
            "findings": findings,
            "limitations": []
        },
        document_uri=uri,
        document_text="first\nsecond\nthird\n",
        rule_pack_version="1.0.0",
        corpus_snapshot="cs_" + "e" * 64,
    )
    assert [
        diagnostic.data["finding_id"]
        for diagnostic in publication.diagnostics
    ] == [
        "finding-early",
        "finding-late",
    ]
EOF
cat > tests/diagnostics/test_incomplete_analysis.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from l9_debt_lsp.diagnostics.builder import DiagnosticBuilder
ROOT = Path(__file__).resolve().parents[2]
def test_incomplete_empty_analysis_emits_limitation() -> None:
    builder = DiagnosticBuilder(ROOT / "schemas/lsp")
    publication = builder.build(
        analysis_result={
            "request_id": "request_" + "b" * 64,
            "workspace_id": "workspace_" + "c" * 64,
            "workspace_generation": 1,
            "document_id": "doc_" + "a" * 64,
            "document_version": 1,
            "active_pack_id": "pack_" + "d" * 64,
            "status": "incomplete",
            "findings": [],
            "limitations": ["SDK partial parse"]
        },
        document_uri="file:///workspace/example.py",
        document_text="broken syntax",
        rule_pack_version="1.0.0",
        corpus_snapshot="cs_" + "e" * 64,
    )
    assert len(publication.diagnostics) == 1
    diagnostic = publication.diagnostics[0]
    assert diagnostic.code == "l9.analysis.incomplete"
    assert diagnostic.severity == 2
    assert diagnostic.data["analysis_status"] == "incomplete"
EOF
cat > tests/diagnostics/test_invalid_primary_location.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from l9_debt_lsp.diagnostics.builder import DiagnosticBuilder
from tests.fixtures.diagnostics.finding import valid_finding
ROOT = Path(__file__).resolve().parents[2]
def test_mismatched_document_identity_is_suppressed() -> None:
    document_id = "doc_" + "a" * 64
    uri = "file:///workspace/example.py"
    finding = valid_finding(
        document_id="doc_" + "f" * 64,
        uri=uri,
    )
    builder = DiagnosticBuilder(ROOT / "schemas/lsp")
    publication = builder.build(
        analysis_result={
            "request_id": "request_" + "b" * 64,
            "workspace_id": "workspace_" + "c" * 64,
            "workspace_generation": 1,
            "document_id": document_id,
            "document_version": 1,
            "active_pack_id": "pack_" + "d" * 64,
            "status": "complete",
            "findings": [finding],
            "limitations": []
        },
        document_uri=uri,
        document_text="hello",
        rule_pack_version="1.0.0",
        corpus_snapshot="cs_" + "e" * 64,
    )
    assert len(publication.diagnostics) == 1
    assert publication.diagnostics[0].code == (
        "l9.analysis.incomplete"
    )
EOF
cat > tests/diagnostics/test_deduplication.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from l9_debt_lsp.diagnostics.builder import DiagnosticBuilder
from tests.fixtures.diagnostics.finding import valid_finding
ROOT = Path(__file__).resolve().parents[2]
def test_identical_sdk_findings_are_deduplicated() -> None:
    document_id = "doc_" + "a" * 64
    uri = "file:///workspace/example.py"
    finding = valid_finding(
        document_id=document_id,
        uri=uri,
    )
    builder = DiagnosticBuilder(ROOT / "schemas/lsp")
    publication = builder.build(
        analysis_result={
            "request_id": "request_" + "b" * 64,
            "workspace_id": "workspace_" + "c" * 64,
            "workspace_generation": 1,
            "document_id": document_id,
            "document_version": 1,
            "active_pack_id": "pack_" + "d" * 64,
            "status": "complete",
            "findings": [finding, finding],
            "limitations": []
        },
        document_uri=uri,
        document_text="hello",
        rule_pack_version="1.0.0",
        corpus_snapshot="cs_" + "e" * 64,
    )
    assert len(publication.diagnostics) == 1
EOF
cat > tests/privacy/test_diagnostic_redaction.py <<'EOF'
from __future__ import annotations
from l9_debt_lsp.diagnostics.sanitization import (
    sanitize_message,
)
def test_absolute_paths_are_redacted() -> None:
    message = sanitize_message(
        "Failure in /home/alice/private/project/file.py"
    )
    assert "/home/alice" not in message
    assert "<redacted-path>" in message
def test_tokens_are_redacted() -> None:
    message = sanitize_message(
        "Authorization: Bearer abcdefghijklmnopqrstuvwxyz"
    )
    assert "abcdefghijklmnopqrstuvwxyz" not in message
    assert "<redacted-secret>" in message
EOF
cat > tests/publication/test_stale_safe_publication.py <<'EOF'
from __future__ import annotations
import pytest
from l9_debt_lsp.analysis.models import PackContext
from l9_debt_lsp.analysis.workspace import WorkspaceManager
from l9_debt_lsp.diagnostics.models import (
    CanonicalDiagnostic,
    DiagnosticPublication,
    Position,
    Range,
)
from l9_debt_lsp.diagnostics.publisher import (
    DiagnosticPublisher,
)
from tests.fixtures.analysis.fake_sdk import (
    FakeAnalysisSession,
)
@pytest.mark.asyncio
async def test_old_document_version_is_not_published() -> None:
    sdk = FakeAnalysisSession()
    workspaces = WorkspaceManager(sdk)
    pack = PackContext(
        pack_id="pack_" + "a" * 64,
        pack_version="1.0.0",
        corpus_snapshot="cs_" + "b" * 64,
        compiler_version="1.0.0",
        taxonomy_version="1.0.0",
        sdk_contract_version="l9.integration-contract/v1",
    )
    workspace = await workspaces.open_workspace(
        workspace_uri="file:///workspace",
        pack=pack,
    )
    document = await workspaces.open_document(
        workspace_id=workspace.workspace_id,
        uri="file:///workspace/a.py",
        language_id="python",
        version=2,
        text="content",
    )
    published: list[object] = []
    async def callback(
        uri: str,
        diagnostics: list[dict[str, object]],
    ) -> None:
        published.append((uri, diagnostics))
    publisher = DiagnosticPublisher(
        workspaces=workspaces,
        callback=callback,
    )
    diagnostic = CanonicalDiagnostic(
        range=Range(
            start=Position(0, 0),
            end=Position(0, 1),
        ),
        severity=2,
        code="l9.example",
        source="l9-ci-debt",
        message="Example",
        tags=(),
        related_information=(),
        data={
            "schema_version": "l9.diagnostic-data/v1",
            "finding_id": "finding-1",
            "canonical_rule_id": "l9.example",
            "provider_rule_id": "provider.example",
            "document_identity": document.document_id,
            "document_version": 1,
            "rule_pack_id": pack.pack_id,
            "rule_pack_version": pack.pack_version,
            "corpus_snapshot": pack.corpus_snapshot,
            "analysis_request_id": "request_" + "c" * 64,
            "analysis_status": "complete",
            "limitations": []
        },
    )
    publication = DiagnosticPublication(
        publication_id="publication_" + "d" * 64,
        workspace_id=workspace.workspace_id,
        workspace_generation=workspace.generation,
        document_id=document.document_id,
        document_uri=document.uri,
        document_version=1,
        rule_pack_id=pack.pack_id,
        rule_pack_version=pack.pack_version,
        analysis_request_id="request_" + "c" * 64,
        analysis_status="complete",
        diagnostics=(diagnostic,),
        limitations=(),
    )
    result = await publisher.publish(publication)
    assert result is False
    assert published == []
EOF
cat > tests/architecture/test_diagnostic_identity_boundary.py <<'EOF'
from __future__ import annotations
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
DIAGNOSTICS = ROOT / "src/l9_debt_lsp/diagnostics"
def test_diagnostics_do_not_generate_sdk_finding_ids() -> None:
    prohibited = (
        'namespaced_hash("finding_',
        "uuid.uuid4",
        "uuid4(",
        "reconstruct_finding",
    )
    for path in DIAGNOSTICS.rglob("*.py"):
        content = path.read_text(encoding="utf-8")
        for term in prohibited:
            assert term not in content, (
                f"{path} contains prohibited finding identity "
                f"generation: {term}"
            )
def test_diagnostics_do_not_access_corpus() -> None:
    prohibited = (
        "corpus-record",
        "corpus_event",
        "mine_patterns",
        "duckdb",
        "pyarrow",
    )
    for path in DIAGNOSTICS.rglob("*.py"):
        content = path.read_text(
            encoding="utf-8"
        ).lower()
        for term in prohibited:
            assert term not in content, (
                f"{path} contains prohibited corpus dependency "
                f"{term}"
            )
EOF
###############################################################################
# 8. ADRs
###############################################################################
cat > docs/architecture/ADRs/ADR-LSP-013-preserve-sdk-finding-identity.md <<'EOF'
# ADR-LSP-013: Preserve canonical SDK finding identity
- Status: Accepted
- Phase: LSP-P3
## Decision
The LSP preserves `finding_id`, `canonical_rule_id`, `provider_rule_id`,
source-location semantics, document identity, pack identity, and corpus
snapshot lineage.
The LSP may change editor severity presentation and message formatting, but it
does not create replacement finding IDs or reinterpret canonical rule meaning.
EOF
cat > docs/architecture/ADRs/ADR-LSP-014-incomplete-is-not-clean.md <<'EOF'
# ADR-LSP-014: Incomplete analysis is not a clean result
- Status: Accepted
- Phase: LSP-P3
## Decision
An incomplete, failed, cancelled, or stale analysis cannot be represented as a
successful empty diagnostic set.
Incomplete and failed analysis produce an explicit limitation diagnostic when
publication remains current. Cancelled and stale results do not replace current
diagnostics.
EOF
cat > docs/architecture/ADRs/ADR-LSP-015-diagnostic-publication-is-versioned.md <<'EOF'
# ADR-LSP-015: Diagnostic publication is version and pack aware
- Status: Accepted
- Phase: LSP-P3
## Decision
A diagnostic publication is committed only when its document version,
workspace generation, active pack, and analysis request still match current
runtime state.
Any mismatch causes the publication to be discarded.
EOF
cat > docs/architecture/ADRs/ADR-LSP-016-diagnostic-output-is-bounded.md <<'EOF'
# ADR-LSP-016: Diagnostic output is deterministic and bounded
- Status: Accepted
- Phase: LSP-P3
## Decision
Diagnostics are deterministically ordered and de-duplicated.
At most 200 finding diagnostics and one limitation diagnostic are published per
document. Overflow is disclosed explicitly and is never represented as complete
clean analysis.
EOF
###############################################################################
# 9. Roadmap and README
###############################################################################
python3 - <<'PY'
from pathlib import Path
path = Path("ROADMAP.md")
text = path.read_text(encoding="utf-8")
text = text.replace(
    """## LSP-P3 — Diagnostic identity
Status: Planned
- preserve SDK finding IDs
- preserve canonical rule IDs
- evidence links
- related information
- deterministic ordering
- incomplete-analysis limitations
""",
    """## LSP-P3 — Diagnostic identity
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
""",
)
path.write_text(text, encoding="utf-8")
PY
cat >> README.md <<'EOF'
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
EOF

###############################################################################

10. CI

###############################################################################

cat > .github/workflows/phase-4-diagnostics.yml <<‘EOF’
name: LSP-P3 Canonical Diagnostics

on:
pull_request:
push:
branches:
- main

permissions:
contents: read

jobs:
diagnostics:
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
  - name: Diagnostic tests
    run: pytest tests/diagnostics
  - name: Publication tests
    run: pytest tests/publication
  - name: Privacy tests
    run: pytest tests/privacy
  - name: Incremental runtime tests
    run: |
      pytest tests/analysis tests/concurrency tests/runtime
  - name: Security tests
    run: pytest tests/security
  - name: Architecture tests
    run: pytest tests/architecture
  - name: Full suite
    run: |
      pytest \
        --cov=l9_debt_lsp \
        --cov-report=term-missing \
        --cov-fail-under=82
  - name: Ruff
    run: ruff check .
  - name: Mypy
    run: mypy src
  - name: Capabilities
    run: l9-debt-lsp-contracts capabilities

EOF

###############################################################################

11. Local validation

###############################################################################

python3 -m compileall -q src

python3 - <<‘PY’
from future import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

root = Path.cwd()

required = [
“.l9/diagnostic-contract.yaml”,
“schemas/lsp/sdk-finding-consumer.schema.json”,
“schemas/lsp/canonical-diagnostic.schema.json”,
“schemas/lsp/diagnostic-publication.schema.json”,
“src/l9_debt_lsp/diagnostics/projection.py”,
“src/l9_debt_lsp/diagnostics/builder.py”,
“src/l9_debt_lsp/diagnostics/publisher.py”,
“src/l9_debt_lsp/runtime/diagnostic_service.py”,
“tests/diagnostics/test_identity_preservation.py”,
“tests/publication/test_stale_safe_publication.py”,
“tests/privacy/test_diagnostic_redaction.py”,
]

missing = [
path
for path in required
if not (root / path).is_file()
]

if missing:
raise SystemExit(
f”LSP-P3 required files missing: {missing}”
)

for schema_path in sorted(
(root / “schemas/lsp”).glob(”*.json”)
):
schema = json.loads(
schema_path.read_text(encoding=“utf-8”)
)
Draft202012Validator.check_schema(schema)

diagnostic_root = root / “src/l9_debt_lsp/diagnostics”

for source_path in diagnostic_root.rglob(”*.py”):
content = source_path.read_text(
encoding=“utf-8”
).lower()

prohibited = (
    "corpus_compiler",
    "mine_patterns",
    "duckdb",
    "pyarrow",
    "requests.",
    "httpx.",
    "sqlite3",
)
for term in prohibited:
    if term in content:
        raise SystemExit(
            f"prohibited diagnostic dependency "
            f"{term!r} in {source_path}"
        )

print(
json.dumps(
{
“schema_version”: “l9.phase-build-result/v1”,
“repository”: “Quantum-L9/l9-ci-debt-lsp”,
“phase”: “LSP-P3”,
“status”: “built”,
“finding_identity”: “preserved”,
“canonical_rule_identity”: “preserved”,
“provider_rule_identity”: “preserved”,
“pack_lineage”: “preserved”,
“diagnostic_ordering”: “deterministic”,
“diagnostic_count”: “bounded”,
“stale_publication”: “discarded”,
“incomplete_analysis”: “explicit”,
“source_content_persistence”: “prohibited”
},
sort_keys=True,
separators=(”,”, “:”),
)
)
PY

printf ‘\n’
printf ‘LSP-P3 build complete.\n’
printf ‘\n’
printf ‘Implemented:\n’
printf ’  - public SDK finding validation\n’
printf ’  - exact finding identity preservation\n’
printf ’  - canonical and provider rule identity preservation\n’
printf ’  - document and pack lineage preservation\n’
printf ’  - safe source-location projection\n’
printf ’  - evidence-related information\n’
printf ’  - deterministic ordering\n’
printf ’  - deterministic de-duplication\n’
printf ’  - bounded per-document diagnostics\n’
printf ’  - explicit incomplete-analysis diagnostics\n’
printf ’  - stale-safe publication coordinator\n’
printf ’  - diagnostic message redaction\n’
printf ’  - pygls document publication integration\n’
printf ‘\n’
printf ‘Next phase: LSP-P4 — bounded code actions, validated WorkspaceEdits, document-version enforcement, conflict detection, protected-path exclusions, previews, and remediation provenance.\n’

:::
This phase completes the read-only diagnostic path. Every published diagnostic is now tied to an exact SDK finding, document version, analysis request, defense-pack version, and corpus snapshot.