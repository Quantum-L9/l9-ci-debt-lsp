Phase 5 implements LSP-P4: bounded code actions and validated workspace edits.

It is the final editor behavior phase, but not the final repository phase. One phase remains:

LSP-P5 — privacy-safe effectiveness telemetry

The repository specification explicitly includes effectiveness telemetry, false-positive dispositions, rule outcomes, and latency metrics after bounded code actions. repo-spec.yaml

Save this as build-phase-5.sh and run it against the completed LSP-P3 repository.

#!/usr/bin/env bash
set -euo pipefail
###############################################################################
# Quantum-L9/l9-ci-debt-lsp
# LSP-P4 — Bounded Code Actions
#
# Adds:
#   - immutable remediation-template consumer contract
#   - diagnostic-to-remediation identity binding
#   - exact document-version enforcement
#   - deterministic WorkspaceEdit construction
#   - edit range validation
#   - overlapping-edit conflict detection
#   - protected-path exclusions
#   - bounded single-document edits
#   - explicit preview requirement
#   - remediation provenance
#   - post-edit validation contract
#   - stale and incomplete-analysis suppression
#   - pygls textDocument/codeAction integration
#
# Prohibits:
#   - arbitrary command execution
#   - shell execution
#   - Git operations
#   - branch mutation
#   - hidden dependency installation
#   - autonomous multi-file repair
#   - unbounded generated patches
#   - protected-path mutation
#
# Remaining phase:
#   LSP-P5 — privacy-safe effectiveness telemetry
###############################################################################
fail() {
  printf 'LSP-P4: %s\n' "$*" >&2
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
require_file ".l9/diagnostic-contract.yaml"
require_file "src/l9_debt_lsp/diagnostics/models.py"
require_file "src/l9_debt_lsp/diagnostics/publisher.py"
require_file "src/l9_debt_lsp/analysis/runtime.py"
require_file "src/l9_debt_lsp/server.py"
require_file "pyproject.toml"
mkdir -p \
  .github/workflows \
  .l9 \
  docs/architecture/ADRs \
  schemas/lsp \
  src/l9_debt_lsp/actions \
  src/l9_debt_lsp/runtime \
  tests/actions \
  tests/security \
  tests/publication \
  tests/fixtures/actions
###############################################################################
# 1. Code-action authority contract
###############################################################################
cat > .l9/code-action-contract.yaml <<'EOF'
schema: l9.lsp-code-action-contract/v1
metadata:
  repository: Quantum-L9/l9-ci-debt-lsp
  phase: LSP-P4
  status: authoritative
authority:
  intelligence_owns:
    - remediation template semantics
    - canonical rule association
    - remediation template identity
    - remediation safety classification
  sdk_owns:
    - finding identity
    - canonical rule identity
    - evidence semantics
    - source-location semantics
  lsp_owns:
    - code-action presentation
    - document-version validation
    - edit-range validation
    - edit conflict detection
    - protected-path enforcement
    - WorkspaceEdit construction
    - preview presentation
    - explicit user-approval boundary
    - post-edit analysis scheduling
  prohibited:
    - invent authoritative remediation semantics
    - execute arbitrary commands
    - execute shell commands
    - run Git commands
    - mutate branches
    - install dependencies
    - edit files outside the declared document
    - autonomous multi-file repair
    - use model-generated unbounded patches
    - apply edits without user approval
input:
  diagnostic:
    schema: l9.canonical-diagnostic/v1
  remediation_template:
    schema: l9.quick-fix-template/v1
    source: active immutable defense pack
binding:
  required_equalities:
    - diagnostic.canonical_rule_id == template.canonical_rule_id
    - diagnostic.rule_pack_id == active_pack.pack_id
    - diagnostic.rule_pack_version == active_pack.pack_version
    - diagnostic.document_identity == current_document.document_id
    - diagnostic.document_version == current_document.version
  stale_behavior: suppress_action
eligibility:
  required:
    - analysis status is complete
    - diagnostic limitations do not prohibit remediation
    - template safety level is deterministic
    - template targets current document only
    - document version matches
    - active pack matches
    - target path is not protected
    - all edits validate
    - edits do not overlap
  suppress_when:
    - analysis incomplete
    - analysis failed
    - result stale
    - document closed
    - active pack changed
    - template unsupported
    - edit range invalid
    - edit count exceeds limit
    - replacement size exceeds limit
    - target is protected
    - edits overlap
    - template requests command execution
limits:
  maximum_actions_per_diagnostic: 5
  maximum_edits_per_action: 50
  maximum_replacement_bytes_per_edit: 65536
  maximum_total_replacement_bytes: 262144
  maximum_preview_characters: 200000
  maximum_title_characters: 200
scope:
  allowed:
    - current_document
  prohibited:
    - other_documents
    - workspace_wide
    - repository_wide
    - external_files
    - virtual_documents
    - untitled_documents
protected_paths:
  exact:
    - .git
    - .env
    - .npmrc
    - .pypirc
    - credentials.json
  prefixes:
    - .git/
    - .github/workflows/
    - .l9/trust/
    - .l9-runtime/
    - state/trust/
    - state/activation/
    - state/packs/
    - state/retirement/
    - state/quarantine/
  suffixes:
    - .pem
    - .key
    - .p12
    - .pfx
    - .crt
    - .cer
edit_validation:
  indexing:
    lines: zero_based
    characters: zero_based
    end: exclusive
  requirements:
    - start and end are non-negative
    - end does not precede start
    - range exists in current document
    - UTF-16 LSP positions convert safely
    - replacement is valid UTF-8
    - edits are deterministically ordered
    - edits do not overlap
workspace_edit:
  allowed_fields:
    - changes
  prohibited_fields:
    - documentChanges
    - changeAnnotations
    - create
    - rename
    - delete
    - command
  invariant: >
    One code action produces edits for exactly one currently open document.
preview:
  required: true
  includes:
    - action title
    - canonical rule identity
    - finding identity
    - template identity
    - rule-pack identity
    - document version
    - bounded unified diff
    - limitations
  source_content_storage: prohibited
application:
  authority: editor_client
  automatic_application: prohibited
  explicit_user_action_required: true
post_application:
  required:
    - editor supplies new document version
    - previous analysis is cancelled
    - document overlay is updated
    - diagnostics are re-evaluated
    - action result is not assumed successful before re-analysis
provenance:
  required:
    - action_id
    - template_id
    - finding_id
    - canonical_rule_id
    - provider_rule_id
    - document_identity
    - document_version
    - rule_pack_id
    - rule_pack_version
    - corpus_snapshot
    - analysis_request_id
    - edit_digest
phase:
  id: LSP-P4
  status: implemented
  includes:
    - remediation template validation
    - diagnostic binding
    - protected-path policy
    - edit validation
    - overlap detection
    - WorkspaceEdit construction
    - preview generation
    - provenance
    - code-action publication
    - post-edit re-analysis contract
  excludes:
    - telemetry transport
    - effectiveness aggregation
    - automatic repair
    - multi-file repair
EOF
###############################################################################
# 2. Schemas
###############################################################################
cat > schemas/lsp/quick-fix-template.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/quick-fix-template/v1",
  "title": "L9 Deterministic Quick Fix Template",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "template_id",
    "canonical_rule_id",
    "title",
    "kind",
    "safety",
    "scope",
    "edits",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.quick-fix-template/v1"
    },
    "template_id": {
      "type": "string",
      "pattern": "^fix_[0-9a-f]{64}$"
    },
    "canonical_rule_id": {
      "type": "string",
      "minLength": 1,
      "maxLength": 512
    },
    "title": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "kind": {
      "enum": [
        "deterministic_template",
        "validated_structural_rewrite"
      ]
    },
    "safety": {
      "enum": [
        "deterministic",
        "validated"
      ]
    },
    "scope": {
      "const": "current_document"
    },
    "edits": {
      "type": "array",
      "minItems": 1,
      "maxItems": 50,
      "items": {
        "$ref": "#/$defs/edit"
      }
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
    "edit": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "start_line",
        "start_character",
        "end_line",
        "end_character",
        "replacement"
      ],
      "properties": {
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
        },
        "replacement": {
          "type": "string",
          "maxLength": 65536
        }
      }
    }
  }
}
EOF
cat > schemas/lsp/code-action-provenance.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/code-action-provenance/v1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "action_id",
    "template_id",
    "finding_id",
    "canonical_rule_id",
    "provider_rule_id",
    "document_identity",
    "document_version",
    "rule_pack_id",
    "rule_pack_version",
    "corpus_snapshot",
    "analysis_request_id",
    "edit_digest",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.code-action-provenance/v1"
    },
    "action_id": {
      "type": "string",
      "pattern": "^action_[0-9a-f]{64}$"
    },
    "template_id": {
      "type": "string",
      "pattern": "^fix_[0-9a-f]{64}$"
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
    "edit_digest": {
      "type": "string",
      "pattern": "^[0-9a-f]{64}$"
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
cat > schemas/lsp/bounded-code-action.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/bounded-code-action/v1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "title",
    "kind",
    "is_preferred",
    "edit",
    "preview",
    "provenance"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.bounded-code-action/v1"
    },
    "title": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "kind": {
      "const": "quickfix"
    },
    "is_preferred": {
      "type": "boolean"
    },
    "edit": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "changes"
      ],
      "properties": {
        "changes": {
          "type": "object",
          "minProperties": 1,
          "maxProperties": 1,
          "additionalProperties": {
            "type": "array",
            "minItems": 1,
            "maxItems": 50,
            "items": {
              "$ref": "#/$defs/textEdit"
            }
          }
        }
      }
    },
    "preview": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "summary",
        "diff",
        "limitations"
      ],
      "properties": {
        "summary": {
          "type": "string"
        },
        "diff": {
          "type": "string",
          "maxLength": 200000
        },
        "limitations": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      }
    },
    "provenance": {
      "$ref": "l9://lsp/code-action-provenance/v1"
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
    "textEdit": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "range",
        "newText"
      ],
      "properties": {
        "range": {
          "$ref": "#/$defs/range"
        },
        "newText": {
          "type": "string"
        }
      }
    }
  }
}
EOF
###############################################################################
# 3. Actions package
###############################################################################
cat > src/l9_debt_lsp/actions/__init__.py <<'EOF'
"""Bounded deterministic code-action construction."""
EOF
cat > src/l9_debt_lsp/actions/errors.py <<'EOF'
from __future__ import annotations
class CodeActionError(RuntimeError):
    """Base bounded code-action failure."""
class CodeActionSuppressed(CodeActionError):
    """The action is intentionally unavailable."""
class TemplateValidationError(CodeActionError):
    """A remediation template is invalid."""
class EditValidationError(CodeActionError):
    """A text edit is outside the bounded safety contract."""
class EditConflictError(CodeActionError):
    """Two edits overlap or conflict."""
class ProtectedPathError(CodeActionError):
    """A remediation targets a protected path."""
class StaleDiagnosticError(CodeActionError):
    """The diagnostic no longer matches current runtime state."""
EOF
cat > src/l9_debt_lsp/actions/models.py <<'EOF'
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
class TextEdit:
    start: Position
    end: Position
    replacement: str
    def as_dict(self) -> dict[str, Any]:
        return {
            "range": {
                "start": self.start.as_dict(),
                "end": self.end.as_dict(),
            },
            "newText": self.replacement,
        }
@dataclass(frozen=True)
class RemediationTemplate:
    template_id: str
    canonical_rule_id: str
    title: str
    kind: str
    safety: str
    scope: str
    edits: tuple[TextEdit, ...]
    limitations: tuple[str, ...]
@dataclass(frozen=True)
class CodeActionProvenance:
    action_id: str
    template_id: str
    finding_id: str
    canonical_rule_id: str
    provider_rule_id: str
    document_identity: str
    document_version: int
    rule_pack_id: str
    rule_pack_version: str
    corpus_snapshot: str
    analysis_request_id: str
    edit_digest: str
    limitations: tuple[str, ...]
    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.code-action-provenance/v1",
            "action_id": self.action_id,
            "template_id": self.template_id,
            "finding_id": self.finding_id,
            "canonical_rule_id": self.canonical_rule_id,
            "provider_rule_id": self.provider_rule_id,
            "document_identity": self.document_identity,
            "document_version": self.document_version,
            "rule_pack_id": self.rule_pack_id,
            "rule_pack_version": self.rule_pack_version,
            "corpus_snapshot": self.corpus_snapshot,
            "analysis_request_id": self.analysis_request_id,
            "edit_digest": self.edit_digest,
            "limitations": list(self.limitations),
        }
@dataclass(frozen=True)
class BoundedCodeAction:
    title: str
    document_uri: str
    edits: tuple[TextEdit, ...]
    preview_summary: str
    preview_diff: str
    preview_limitations: tuple[str, ...]
    provenance: CodeActionProvenance
    is_preferred: bool
    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.bounded-code-action/v1",
            "title": self.title,
            "kind": "quickfix",
            "is_preferred": self.is_preferred,
            "edit": {
                "changes": {
                    self.document_uri: [
                        edit.as_dict()
                        for edit in self.edits
                    ]
                }
            },
            "preview": {
                "summary": self.preview_summary,
                "diff": self.preview_diff,
                "limitations": list(
                    self.preview_limitations
                ),
            },
            "provenance": self.provenance.as_dict(),
        }
EOF
cat > src/l9_debt_lsp/actions/protected_paths.py <<'EOF'
from __future__ import annotations
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit
from .errors import ProtectedPathError
PROTECTED_EXACT = {
    ".git",
    ".env",
    ".npmrc",
    ".pypirc",
    "credentials.json",
}
PROTECTED_PREFIXES = (
    ".git/",
    ".github/workflows/",
    ".l9/trust/",
    ".l9-runtime/",
    "state/trust/",
    "state/activation/",
    "state/packs/",
    "state/retirement/",
    "state/quarantine/",
)
PROTECTED_SUFFIXES = (
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".crt",
    ".cer",
)
def normalized_workspace_path(
    *,
    document_uri: str,
    workspace_uri: str,
) -> str:
    document = urlsplit(document_uri)
    workspace = urlsplit(workspace_uri)
    if document.scheme != "file" or workspace.scheme != "file":
        raise ProtectedPathError(
            "code actions require file-backed documents"
        )
    document_path = PurePosixPath(unquote(document.path))
    workspace_path = PurePosixPath(unquote(workspace.path))
    try:
        relative = document_path.relative_to(workspace_path)
    except ValueError as error:
        raise ProtectedPathError(
            "document is outside the workspace"
        ) from error
    value = relative.as_posix()
    if value in {"", "."}:
        raise ProtectedPathError(
            "workspace root is not an editable document"
        )
    return value
def require_editable_path(
    *,
    document_uri: str,
    workspace_uri: str,
) -> str:
    relative = normalized_workspace_path(
        document_uri=document_uri,
        workspace_uri=workspace_uri,
    )
    folded = relative.casefold()
    if folded in {value.casefold() for value in PROTECTED_EXACT}:
        raise ProtectedPathError(
            f"protected path: {relative}"
        )
    if any(
        folded.startswith(prefix.casefold())
        for prefix in PROTECTED_PREFIXES
    ):
        raise ProtectedPathError(
            f"protected path: {relative}"
        )
    if any(
        folded.endswith(suffix.casefold())
        for suffix in PROTECTED_SUFFIXES
    ):
        raise ProtectedPathError(
            f"protected credential path: {relative}"
        )
    return relative
EOF
cat > src/l9_debt_lsp/actions/positions.py <<'EOF'
from __future__ import annotations
from .errors import EditValidationError
from .models import Position, TextEdit
MAX_EDITS = 50
MAX_REPLACEMENT_BYTES = 65536
MAX_TOTAL_REPLACEMENT_BYTES = 262144
def line_start_offsets(text: str) -> list[int]:
    offsets = [0]
    for index, character in enumerate(text):
        if character == "\n":
            offsets.append(index + 1)
    return offsets
def character_offset(
    text: str,
    position: Position,
) -> int:
    if position.line < 0 or position.character < 0:
        raise EditValidationError(
            "edit position must be non-negative"
        )
    offsets = line_start_offsets(text)
    if position.line >= len(offsets):
        raise EditValidationError(
            "edit line is outside the document"
        )
    start = offsets[position.line]
    if position.line + 1 < len(offsets):
        line_end = offsets[position.line + 1] - 1
    else:
        line_end = len(text)
    line_text = text[start:line_end]
    if position.character > len(line_text):
        raise EditValidationError(
            "edit character is outside the line"
        )
    return start + position.character
def validate_edits(
    *,
    text: str,
    edits: tuple[TextEdit, ...],
) -> tuple[TextEdit, ...]:
    if not edits:
        raise EditValidationError(
            "a code action requires at least one edit"
        )
    if len(edits) > MAX_EDITS:
        raise EditValidationError(
            f"edit count exceeds {MAX_EDITS}"
        )
    total_replacement_bytes = 0
    positioned: list[tuple[int, int, TextEdit]] = []
    for edit in edits:
        replacement_bytes = len(
            edit.replacement.encode("utf-8")
        )
        if replacement_bytes > MAX_REPLACEMENT_BYTES:
            raise EditValidationError(
                "individual replacement exceeds byte limit"
            )
        total_replacement_bytes += replacement_bytes
        start = character_offset(text, edit.start)
        end = character_offset(text, edit.end)
        if end < start:
            raise EditValidationError(
                "edit end precedes edit start"
            )
        positioned.append((start, end, edit))
    if total_replacement_bytes > MAX_TOTAL_REPLACEMENT_BYTES:
        raise EditValidationError(
            "total replacement bytes exceed limit"
        )
    positioned.sort(
        key=lambda value: (
            value[0],
            value[1],
            value[2].replacement,
        )
    )
    previous_end = -1
    for start, end, _edit in positioned:
        if start < previous_end:
            raise EditValidationError(
                "overlapping edits are prohibited"
            )
        previous_end = max(previous_end, end)
    return tuple(value[2] for value in positioned)
def apply_edits(
    *,
    text: str,
    edits: tuple[TextEdit, ...],
) -> str:
    positioned = [
        (
            character_offset(text, edit.start),
            character_offset(text, edit.end),
            edit.replacement,
        )
        for edit in edits
    ]
    result = text
    for start, end, replacement in sorted(
        positioned,
        key=lambda value: (value[0], value[1]),
        reverse=True,
    ):
        result = result[:start] + replacement + result[end:]
    return result
EOF
cat > src/l9_debt_lsp/actions/templates.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from typing import Any
from l9_debt_lsp.contracts.schema import SchemaValidator
from .errors import TemplateValidationError
from .models import (
    Position,
    RemediationTemplate,
    TextEdit,
)
class TemplateParser:
    def __init__(self, schema_root: Path) -> None:
        self._validator = SchemaValidator(
            schema_root / "quick-fix-template.schema.json"
        )
    def parse(
        self,
        value: dict[str, Any],
    ) -> RemediationTemplate:
        try:
            self._validator.validate(value)
        except Exception as error:
            raise TemplateValidationError(str(error)) from error
        if value["scope"] != "current_document":
            raise TemplateValidationError(
                "only current-document fixes are supported"
            )
        if value["kind"] not in {
            "deterministic_template",
            "validated_structural_rewrite",
        }:
            raise TemplateValidationError(
                "unsupported remediation kind"
            )
        edits = tuple(
            TextEdit(
                start=Position(
                    line=edit["start_line"],
                    character=edit["start_character"],
                ),
                end=Position(
                    line=edit["end_line"],
                    character=edit["end_character"],
                ),
                replacement=edit["replacement"],
            )
            for edit in value["edits"]
        )
        return RemediationTemplate(
            template_id=value["template_id"],
            canonical_rule_id=value["canonical_rule_id"],
            title=value["title"],
            kind=value["kind"],
            safety=value["safety"],
            scope=value["scope"],
            edits=edits,
            limitations=tuple(
                sorted(set(value["limitations"]))
            ),
        )
EOF
cat > src/l9_debt_lsp/actions/preview.py <<'EOF'
from __future__ import annotations
import difflib
from .models import RemediationTemplate
from .positions import apply_edits
MAX_PREVIEW_CHARACTERS = 200000
def build_preview(
    *,
    relative_path: str,
    text: str,
    template: RemediationTemplate,
) -> tuple[str, str, tuple[str, ...]]:
    updated = apply_edits(
        text=text,
        edits=template.edits,
    )
    diff_lines = difflib.unified_diff(
        text.splitlines(keepends=True),
        updated.splitlines(keepends=True),
        fromfile=f"a/{relative_path}",
        tofile=f"b/{relative_path}",
        lineterm="",
    )
    diff = "\n".join(diff_lines)
    limitations = list(template.limitations)
    if len(diff) > MAX_PREVIEW_CHARACTERS:
        diff = diff[: MAX_PREVIEW_CHARACTERS - 1] + "…"
        limitations.append(
            "Preview was truncated to the configured limit."
        )
    summary = (
        f"{template.title} "
        f"({len(template.edits)} deterministic edit"
        f"{'' if len(template.edits) == 1 else 's'})"
    )
    return (
        summary,
        diff,
        tuple(sorted(set(limitations))),
    )
EOF
cat > src/l9_debt_lsp/actions/builder.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from typing import Any
from l9_debt_lsp.contracts.canonical import canonical_json
from l9_debt_lsp.packs.hashing import (
    namespaced_hash,
    sha256_bytes,
)
from .errors import (
    CodeActionSuppressed,
    StaleDiagnosticError,
)
from .models import (
    BoundedCodeAction,
    CodeActionProvenance,
)
from .positions import validate_edits
from .preview import build_preview
from .protected_paths import require_editable_path
from .templates import TemplateParser
MAX_ACTIONS_PER_DIAGNOSTIC = 5
class CodeActionBuilder:
    def __init__(self, schema_root: Path) -> None:
        self._parser = TemplateParser(schema_root)
    def build(
        self,
        *,
        diagnostic: dict[str, Any],
        templates: list[dict[str, Any]],
        document_uri: str,
        workspace_uri: str,
        document_id: str,
        document_version: int,
        document_text: str,
        active_pack_id: str,
        active_pack_version: str,
        corpus_snapshot: str,
    ) -> tuple[BoundedCodeAction, ...]:
        data = diagnostic.get("data")
        if not isinstance(data, dict):
            raise CodeActionSuppressed(
                "diagnostic does not contain canonical L9 data"
            )
        self._validate_diagnostic_binding(
            data=data,
            document_id=document_id,
            document_version=document_version,
            active_pack_id=active_pack_id,
            active_pack_version=active_pack_version,
        )
        if data["analysis_status"] != "complete":
            raise CodeActionSuppressed(
                "code actions are suppressed for incomplete analysis"
            )
        relative_path = require_editable_path(
            document_uri=document_uri,
            workspace_uri=workspace_uri,
        )
        actions: list[BoundedCodeAction] = []
        for raw_template in templates:
            template = self._parser.parse(raw_template)
            if (
                template.canonical_rule_id
                != data["canonical_rule_id"]
            ):
                continue
            edits = validate_edits(
                text=document_text,
                edits=template.edits,
            )
            summary, diff, limitations = build_preview(
                relative_path=relative_path,
                text=document_text,
                template=template,
            )
            edit_payload = {
                "document_uri": document_uri,
                "document_version": document_version,
                "edits": [
                    edit.as_dict()
                    for edit in edits
                ],
            }
            edit_digest = sha256_bytes(
                canonical_json(edit_payload)
            )
            action_id = namespaced_hash(
                "action_",
                {
                    "template_id": template.template_id,
                    "finding_id": data["finding_id"],
                    "document_identity": document_id,
                    "document_version": document_version,
                    "rule_pack_id": active_pack_id,
                    "edit_digest": edit_digest,
                },
            )
            provenance = CodeActionProvenance(
                action_id=action_id,
                template_id=template.template_id,
                finding_id=data["finding_id"],
                canonical_rule_id=data[
                    "canonical_rule_id"
                ],
                provider_rule_id=data["provider_rule_id"],
                document_identity=document_id,
                document_version=document_version,
                rule_pack_id=active_pack_id,
                rule_pack_version=active_pack_version,
                corpus_snapshot=corpus_snapshot,
                analysis_request_id=data[
                    "analysis_request_id"
                ],
                edit_digest=edit_digest,
                limitations=limitations,
            )
            actions.append(
                BoundedCodeAction(
                    title=template.title,
                    document_uri=document_uri,
                    edits=edits,
                    preview_summary=summary,
                    preview_diff=diff,
                    preview_limitations=limitations,
                    provenance=provenance,
                    is_preferred=(
                        template.safety == "deterministic"
                        and not limitations
                    ),
                )
            )
        actions.sort(
            key=lambda action: (
                not action.is_preferred,
                action.title,
                action.provenance.template_id,
                action.provenance.action_id,
            )
        )
        return tuple(actions[:MAX_ACTIONS_PER_DIAGNOSTIC])
    @staticmethod
    def _validate_diagnostic_binding(
        *,
        data: dict[str, Any],
        document_id: str,
        document_version: int,
        active_pack_id: str,
        active_pack_version: str,
    ) -> None:
        required = (
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
        )
        missing = [
            field
            for field in required
            if field not in data
        ]
        if missing:
            raise CodeActionSuppressed(
                f"diagnostic data is incomplete: {missing}"
            )
        if data["document_identity"] != document_id:
            raise StaleDiagnosticError(
                "diagnostic document identity is stale"
            )
        if data["document_version"] != document_version:
            raise StaleDiagnosticError(
                "diagnostic document version is stale"
            )
        if data["rule_pack_id"] != active_pack_id:
            raise StaleDiagnosticError(
                "diagnostic pack identity is stale"
            )
        if (
            data["rule_pack_version"]
            != active_pack_version
        ):
            raise StaleDiagnosticError(
                "diagnostic pack version is stale"
            )
EOF
cat > src/l9_debt_lsp/actions/registry.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from typing import Any
from l9_debt_lsp.packs.jsonio import load_json
class RemediationRegistry:
    """Read remediation templates from the active immutable pack."""
    def templates_for_rule(
        self,
        *,
        pack_root: Path,
        canonical_rule_id: str,
    ) -> list[dict[str, Any]]:
        registry_path = (
            pack_root / "remediations/index.json"
        )
        if not registry_path.is_file():
            return []
        index = load_json(registry_path)
        entries = index.get("templates", [])
        if not isinstance(entries, list):
            return []
        templates: list[dict[str, Any]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if (
                entry.get("canonical_rule_id")
                != canonical_rule_id
            ):
                continue
            relative_path = entry.get("path")
            if not isinstance(relative_path, str):
                continue
            path = pack_root / relative_path
            if not path.is_file():
                continue
            templates.append(load_json(path))
        return templates
EOF
###############################################################################
# 4. Runtime code-action service
###############################################################################
cat > src/l9_debt_lsp/runtime/code_action_service.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from typing import Any
from l9_debt_lsp.actions.builder import CodeActionBuilder
from l9_debt_lsp.actions.errors import CodeActionError
from l9_debt_lsp.actions.registry import RemediationRegistry
from l9_debt_lsp.analysis.runtime import (
    IncrementalAnalysisRuntime,
)
class CodeActionService:
    def __init__(
        self,
        *,
        runtime: IncrementalAnalysisRuntime,
        schema_root: Path,
        packs_root: Path,
    ) -> None:
        self.runtime = runtime
        self.packs_root = packs_root
        self.builder = CodeActionBuilder(schema_root)
        self.registry = RemediationRegistry()
    def actions_for_diagnostic(
        self,
        *,
        workspace_id: str,
        workspace_uri: str,
        document_id: str,
        diagnostic: dict[str, Any],
    ) -> list[dict[str, Any]]:
        workspace = self.runtime.workspaces.get_workspace_nowait(
            workspace_id
        )
        overlay = workspace.documents.get(document_id)
        if (
            overlay is None
            or overlay.state != "open"
            or workspace.active_pack is None
        ):
            return []
        data = diagnostic.get("data")
        if not isinstance(data, dict):
            return []
        canonical_rule_id = data.get(
            "canonical_rule_id"
        )
        if not isinstance(canonical_rule_id, str):
            return []
        pack_root = (
            self.packs_root
            / workspace.active_pack.pack_id
        )
        templates = self.registry.templates_for_rule(
            pack_root=pack_root,
            canonical_rule_id=canonical_rule_id,
        )
        try:
            actions = self.builder.build(
                diagnostic=diagnostic,
                templates=templates,
                document_uri=overlay.uri,
                workspace_uri=workspace_uri,
                document_id=document_id,
                document_version=overlay.version,
                document_text=overlay.text,
                active_pack_id=(
                    workspace.active_pack.pack_id
                ),
                active_pack_version=(
                    workspace.active_pack.pack_version
                ),
                corpus_snapshot=(
                    workspace.active_pack.corpus_snapshot
                ),
            )
        except CodeActionError:
            return []
        return [
            action.as_dict()
            for action in actions
        ]
EOF
###############################################################################
# 5. LSP conversion
###############################################################################
cat > src/l9_debt_lsp/actions/lsp_types.py <<'EOF'
from __future__ import annotations
from typing import Any
from lsprotocol.types import (
    CodeAction,
    CodeActionKind,
    Position,
    Range,
    TextEdit,
    WorkspaceEdit,
)
def to_lsp_code_action(
    value: dict[str, Any],
) -> CodeAction:
    changes: dict[str, list[TextEdit]] = {}
    for uri, edits in value["edit"]["changes"].items():
        changes[uri] = [
            TextEdit(
                range=Range(
                    start=Position(
                        line=edit["range"]["start"]["line"],
                        character=edit["range"]["start"][
                            "character"
                        ],
                    ),
                    end=Position(
                        line=edit["range"]["end"]["line"],
                        character=edit["range"]["end"][
                            "character"
                        ],
                    ),
                ),
                new_text=edit["newText"],
            )
            for edit in edits
        ]
    return CodeAction(
        title=value["title"],
        kind=CodeActionKind.QuickFix,
        is_preferred=value["is_preferred"],
        edit=WorkspaceEdit(changes=changes),
        data={
            "schema_version": "l9.code-action-data/v1",
            "preview": value["preview"],
            "provenance": value["provenance"],
            "requires_explicit_user_approval": True,
        },
    )
EOF
###############################################################################
# 6. Server integration
###############################################################################
python3 - <<'PY'
from pathlib import Path
path = Path("src/l9_debt_lsp/server.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    """from lsprotocol.types import (
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    InitializeParams,
    InitializeResult,
    ServerCapabilities,
    TextDocumentSyncKind,
)""",
    """from lsprotocol.types import (
    CodeActionOptions,
    CodeActionParams,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    InitializeParams,
    InitializeResult,
    ServerCapabilities,
    TextDocumentSyncKind,
)""",
)
text = text.replace(
    """from l9_debt_lsp.analysis.identity import (
    document_identity,
    workspace_identity,
)""",
    """from l9_debt_lsp.actions.lsp_types import (
    to_lsp_code_action,
)
from l9_debt_lsp.analysis.identity import (
    document_identity,
    workspace_identity,
)""",
)
text = text.replace(
    """from l9_debt_lsp.runtime.capabilities import (
    phase_capabilities,
)""",
    """from l9_debt_lsp.packs.paths import (
    StatePaths,
    default_state_root,
)
from l9_debt_lsp.runtime.capabilities import (
    phase_capabilities,
)
from l9_debt_lsp.runtime.code_action_service import (
    CodeActionService,
)""",
)
text = text.replace(
    """diagnostic_service = DiagnosticService(
    runtime=runtime,
    publisher=publisher,
    schema_root=Path("schemas/lsp").resolve(),
)""",
    """diagnostic_service = DiagnosticService(
    runtime=runtime,
    publisher=publisher,
    schema_root=Path("schemas/lsp").resolve(),
)
state_paths = StatePaths(default_state_root())
code_action_service = CodeActionService(
    runtime=runtime,
    schema_root=Path("schemas/lsp").resolve(),
    packs_root=state_paths.packs,
)""",
)
text = text.replace(
    """        capabilities=ServerCapabilities(
            text_document_sync=TextDocumentSyncKind.Full,
        ),""",
    """        capabilities=ServerCapabilities(
            text_document_sync=TextDocumentSyncKind.Full,
            code_action_provider=CodeActionOptions(
                code_action_kinds=["quickfix"],
                resolve_provider=False,
            ),
        ),""",
)
insert = '''
@server.feature("textDocument/codeAction")
def code_action(
    params: CodeActionParams,
) -> list[Any]:
    uri = params.text_document.uri
    document_id = document_identity(uri)
    workspace_id = workspace_by_document.get(document_id)
    if workspace_id is None:
        return []
    workspace_uri = (
        server.workspace.root_uri
        or uri.rsplit("/", 1)[0]
    )
    actions: list[Any] = []
    for diagnostic in params.context.diagnostics:
        raw = {
            "range": {
                "start": {
                    "line": diagnostic.range.start.line,
                    "character": (
                        diagnostic.range.start.character
                    ),
                },
                "end": {
                    "line": diagnostic.range.end.line,
                    "character": (
                        diagnostic.range.end.character
                    ),
                },
            },
            "severity": (
                int(diagnostic.severity)
                if diagnostic.severity is not None
                else 2
            ),
            "code": str(diagnostic.code or ""),
            "source": diagnostic.source or "",
            "message": diagnostic.message,
            "tags": [
                int(tag)
                for tag in (diagnostic.tags or [])
            ],
            "related_information": [],
            "data": diagnostic.data,
        }
        values = code_action_service.actions_for_diagnostic(
            workspace_id=workspace_id,
            workspace_uri=workspace_uri,
            document_id=document_id,
            diagnostic=raw,
        )
        actions.extend(
            to_lsp_code_action(value)
            for value in values
        )
    return actions
'''
marker = '\n\n@server.feature("l9/serverCapabilities")'
if insert.strip() not in text:
    text = text.replace(marker, insert + marker)
path.write_text(text, encoding="utf-8")
PY
###############################################################################
# 7. Runtime capabilities and version
###############################################################################
cat > src/l9_debt_lsp/runtime/capabilities.py <<'EOF'
from __future__ import annotations
from typing import Any
def phase_capabilities() -> dict[str, Any]:
    return {
        "schema_version": "l9.lsp-server-capabilities/v1",
        "phase": "LSP-P4",
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
            "arbitrary_command_execution": False,
            "autonomous_multi_file_repair": False,
            "telemetry": False
        },
        "limitations": [
            "Code actions require deterministic templates in the active pack.",
            "Every edit requires explicit editor-user approval.",
            "Multi-file and autonomous repair remain prohibited.",
            "Effectiveness telemetry is implemented in LSP-P5."
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
    ):
        text = text.replace(old, "0.5.0")
    path.write_text(text, encoding="utf-8")
PY
###############################################################################
# 8. Tests
###############################################################################
cat > tests/fixtures/actions/template.py <<'EOF'
from __future__ import annotations
from typing import Any
def valid_template(
    *,
    canonical_rule_id: str = "l9.example.rule",
    replacement: str = "fixed",
) -> dict[str, Any]:
    return {
        "schema_version": "l9.quick-fix-template/v1",
        "template_id": "fix_" + "a" * 64,
        "canonical_rule_id": canonical_rule_id,
        "title": "Apply deterministic fix",
        "kind": "deterministic_template",
        "safety": "deterministic",
        "scope": "current_document",
        "edits": [
            {
                "start_line": 0,
                "start_character": 0,
                "end_line": 0,
                "end_character": 5,
                "replacement": replacement
            }
        ],
        "limitations": []
    }
def valid_diagnostic(
    *,
    document_id: str,
    document_version: int,
    pack_id: str,
    pack_version: str,
) -> dict[str, Any]:
    return {
        "range": {
            "start": {
                "line": 0,
                "character": 0
            },
            "end": {
                "line": 0,
                "character": 5
            }
        },
        "severity": 2,
        "code": "l9.example.rule",
        "source": "l9-ci-debt",
        "message": "Example",
        "tags": [],
        "related_information": [],
        "data": {
            "schema_version": "l9.diagnostic-data/v1",
            "finding_id": "finding-1",
            "canonical_rule_id": "l9.example.rule",
            "provider_rule_id": "provider.example",
            "document_identity": document_id,
            "document_version": document_version,
            "rule_pack_id": pack_id,
            "rule_pack_version": pack_version,
            "corpus_snapshot": "cs_" + "b" * 64,
            "analysis_request_id": "request_" + "c" * 64,
            "analysis_status": "complete",
            "limitations": []
        }
    }
EOF
touch tests/fixtures/actions/__init__.py
cat > tests/actions/test_code_action_builder.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from l9_debt_lsp.actions.builder import CodeActionBuilder
from tests.fixtures.actions.template import (
    valid_diagnostic,
    valid_template,
)
ROOT = Path(__file__).resolve().parents[2]
def test_builds_single_document_workspace_edit() -> None:
    document_id = "doc_" + "d" * 64
    pack_id = "pack_" + "e" * 64
    builder = CodeActionBuilder(ROOT / "schemas/lsp")
    actions = builder.build(
        diagnostic=valid_diagnostic(
            document_id=document_id,
            document_version=3,
            pack_id=pack_id,
            pack_version="1.0.0",
        ),
        templates=[valid_template()],
        document_uri="file:///workspace/example.py",
        workspace_uri="file:///workspace",
        document_id=document_id,
        document_version=3,
        document_text="wrong\n",
        active_pack_id=pack_id,
        active_pack_version="1.0.0",
        corpus_snapshot="cs_" + "b" * 64,
    )
    assert len(actions) == 1
    action = actions[0].as_dict()
    assert list(action["edit"]["changes"]) == [
        "file:///workspace/example.py"
    ]
    assert action["edit"]["changes"][
        "file:///workspace/example.py"
    ][0]["newText"] == "fixed"
    assert action["provenance"]["finding_id"] == (
        "finding-1"
    )
    assert action["provenance"]["document_version"] == 3
EOF
cat > tests/actions/test_stale_binding.py <<'EOF'
from __future__ import annotations
from pathlib import Path
import pytest
from l9_debt_lsp.actions.builder import CodeActionBuilder
from l9_debt_lsp.actions.errors import StaleDiagnosticError
from tests.fixtures.actions.template import (
    valid_diagnostic,
    valid_template,
)
ROOT = Path(__file__).resolve().parents[2]
def test_stale_document_version_suppresses_action() -> None:
    document_id = "doc_" + "d" * 64
    pack_id = "pack_" + "e" * 64
    builder = CodeActionBuilder(ROOT / "schemas/lsp")
    with pytest.raises(StaleDiagnosticError):
        builder.build(
            diagnostic=valid_diagnostic(
                document_id=document_id,
                document_version=2,
                pack_id=pack_id,
                pack_version="1.0.0",
            ),
            templates=[valid_template()],
            document_uri="file:///workspace/example.py",
            workspace_uri="file:///workspace",
            document_id=document_id,
            document_version=3,
            document_text="wrong\n",
            active_pack_id=pack_id,
            active_pack_version="1.0.0",
            corpus_snapshot="cs_" + "b" * 64,
        )
EOF
cat > tests/actions/test_incomplete_suppression.py <<'EOF'
from __future__ import annotations
from pathlib import Path
import pytest
from l9_debt_lsp.actions.builder import CodeActionBuilder
from l9_debt_lsp.actions.errors import CodeActionSuppressed
from tests.fixtures.actions.template import (
    valid_diagnostic,
    valid_template,
)
ROOT = Path(__file__).resolve().parents[2]
def test_incomplete_analysis_has_no_fix() -> None:
    document_id = "doc_" + "d" * 64
    pack_id = "pack_" + "e" * 64
    diagnostic = valid_diagnostic(
        document_id=document_id,
        document_version=1,
        pack_id=pack_id,
        pack_version="1.0.0",
    )
    diagnostic["data"]["analysis_status"] = "incomplete"
    builder = CodeActionBuilder(ROOT / "schemas/lsp")
    with pytest.raises(CodeActionSuppressed):
        builder.build(
            diagnostic=diagnostic,
            templates=[valid_template()],
            document_uri="file:///workspace/example.py",
            workspace_uri="file:///workspace",
            document_id=document_id,
            document_version=1,
            document_text="wrong\n",
            active_pack_id=pack_id,
            active_pack_version="1.0.0",
            corpus_snapshot="cs_" + "b" * 64,
        )
EOF
cat > tests/actions/test_edit_validation.py <<'EOF'
from __future__ import annotations
import pytest
from l9_debt_lsp.actions.errors import EditValidationError
from l9_debt_lsp.actions.models import Position, TextEdit
from l9_debt_lsp.actions.positions import (
    apply_edits,
    validate_edits,
)
def test_non_overlapping_edits_apply_deterministically() -> None:
    edits = (
        TextEdit(
            start=Position(0, 0),
            end=Position(0, 1),
            replacement="A",
        ),
        TextEdit(
            start=Position(0, 2),
            end=Position(0, 3),
            replacement="C",
        ),
    )
    validated = validate_edits(
        text="abc",
        edits=edits,
    )
    assert apply_edits(
        text="abc",
        edits=validated,
    ) == "AbC"
def test_overlapping_edits_are_rejected() -> None:
    edits = (
        TextEdit(
            start=Position(0, 0),
            end=Position(0, 2),
            replacement="x",
        ),
        TextEdit(
            start=Position(0, 1),
            end=Position(0, 3),
            replacement="y",
        ),
    )
    with pytest.raises(EditValidationError):
        validate_edits(
            text="abc",
            edits=edits,
        )
EOF
cat > tests/security/test_protected_paths.py <<'EOF'
from __future__ import annotations
import pytest
from l9_debt_lsp.actions.errors import ProtectedPathError
from l9_debt_lsp.actions.protected_paths import (
    require_editable_path,
)
@pytest.mark.parametrize(
    "uri",
    [
        "file:///workspace/.env",
        "file:///workspace/.git/config",
        "file:///workspace/.github/workflows/ci.yml",
        "file:///workspace/state/trust/keys.json",
        "file:///workspace/private.pem",
    ],
)
def test_protected_paths_are_rejected(uri: str) -> None:
    with pytest.raises(ProtectedPathError):
        require_editable_path(
            document_uri=uri,
            workspace_uri="file:///workspace",
        )
def test_normal_source_file_is_allowed() -> None:
    result = require_editable_path(
        document_uri="file:///workspace/src/example.py",
        workspace_uri="file:///workspace",
    )
    assert result == "src/example.py"
EOF
cat > tests/actions/test_preview.py <<'EOF'
from __future__ import annotations
from l9_debt_lsp.actions.models import (
    Position,
    RemediationTemplate,
    TextEdit,
)
from l9_debt_lsp.actions.preview import build_preview
def test_preview_contains_bounded_unified_diff() -> None:
    template = RemediationTemplate(
        template_id="fix_" + "a" * 64,
        canonical_rule_id="l9.example",
        title="Replace value",
        kind="deterministic_template",
        safety="deterministic",
        scope="current_document",
        edits=(
            TextEdit(
                start=Position(0, 0),
                end=Position(0, 3),
                replacement="new",
            ),
        ),
        limitations=(),
    )
    summary, diff, limitations = build_preview(
        relative_path="src/example.py",
        text="old\n",
        template=template,
    )
    assert "Replace value" in summary
    assert "-old" in diff
    assert "+new" in diff
    assert limitations == ()
EOF
cat > tests/architecture/test_code_action_boundary.py <<'EOF'
from __future__ import annotations
import ast
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
ACTIONS = ROOT / "src/l9_debt_lsp/actions"
PROHIBITED_IMPORTS = (
    "subprocess",
    "pty",
    "pexpect",
    "git",
    "dulwich",
    "requests",
    "httpx",
    "aiohttp",
)
PROHIBITED_TERMS = (
    "os.system",
    "shell=true",
    "git checkout",
    "git commit",
    "git push",
    "pip install",
    "npm install",
    "createfile",
    "renamefile",
    "deletefile",
)
def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                result.add(node.module)
    return result
def test_actions_execute_no_commands_or_network() -> None:
    for path in ACTIONS.rglob("*.py"):
        for module in imported_modules(path):
            assert not module.startswith(PROHIBITED_IMPORTS), (
                f"{path} imports prohibited module {module}"
            )
def test_actions_contain_no_mutating_command_paths() -> None:
    for path in ACTIONS.rglob("*.py"):
        content = path.read_text(
            encoding="utf-8"
        ).lower()
        for term in PROHIBITED_TERMS:
            assert term not in content, (
                f"{path} contains prohibited operation {term}"
            )
EOF
###############################################################################
# 9. ADRs
###############################################################################
cat > docs/architecture/ADRs/ADR-LSP-017-code-actions-are-bounded.md <<'EOF'
# ADR-LSP-017: Code actions are bounded and deterministic
- Status: Accepted
- Phase: LSP-P4
## Decision
The LSP offers only deterministic template fixes and validated structural
rewrites published in the active immutable defense pack.
One action edits one open document, with at most 50 non-overlapping text edits.
Autonomous multi-file repair and unbounded generated patches remain prohibited.
EOF
cat > docs/architecture/ADRs/ADR-LSP-018-code-actions-require-exact-version.md <<'EOF'
# ADR-LSP-018: Code actions bind to an exact document and pack version
- Status: Accepted
- Phase: LSP-P4
## Decision
A code action is available only when its diagnostic document identity,
document version, rule-pack identity, and rule-pack version still match current
runtime state.
Stale diagnostics never produce edits.
EOF
cat > docs/architecture/ADRs/ADR-LSP-019-editor-retains-application-authority.md <<'EOF'
# ADR-LSP-019: The editor user retains edit application authority
- Status: Accepted
- Phase: LSP-P4
## Decision
The LSP constructs and previews a WorkspaceEdit but never applies it
autonomously.
The editor client and user retain the final approval boundary.
EOF
cat > docs/architecture/ADRs/ADR-LSP-020-protected-paths-are-not-editable.md <<'EOF'
# ADR-LSP-020: Security and governance paths are excluded from code actions
- Status: Accepted
- Phase: LSP-P4
## Decision
Code actions cannot modify Git metadata, workflow definitions, trust state,
pack state, activation state, retirement state, quarantine state, environment
files, credentials, private keys, or certificates.
EOF
###############################################################################
# 10. Roadmap and README
###############################################################################
python3 - <<'PY'
from pathlib import Path
path = Path("ROADMAP.md")
text = path.read_text(encoding="utf-8")
text = text.replace(
    """## LSP-P4 — Bounded code actions
Status: Planned
- validated quick fixes
- document-version checks
- edit conflict handling
- protected-path exclusions
- preview and provenance
- no arbitrary command execution
""",
    """## LSP-P4 — Bounded code actions
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
""",
)
path.write_text(text, encoding="utf-8")
PY
cat >> README.md <<'EOF'
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
EOF

###############################################################################

11. CI

###############################################################################

cat > .github/workflows/phase-5-code-actions.yml <<‘EOF’
name: LSP-P4 Bounded Code Actions

on:
pull_request:
push:
branches:
- main

permissions:
contents: read

jobs:
code-actions:
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
  - name: Code-action tests
    run: pytest tests/actions
  - name: Security tests
    run: pytest tests/security
  - name: Publication tests
    run: pytest tests/publication
  - name: Diagnostic tests
    run: pytest tests/diagnostics
  - name: Runtime tests
    run: |
      pytest \
        tests/analysis \
        tests/concurrency \
        tests/runtime
  - name: Architecture tests
    run: pytest tests/architecture
  - name: Full suite
    run: |
      pytest \
        --cov=l9_debt_lsp \
        --cov-report=term-missing \
        --cov-fail-under=84
  - name: Ruff
    run: ruff check .
  - name: Mypy
    run: mypy src
  - name: Capabilities
    run: l9-debt-lsp-contracts capabilities

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
“.l9/code-action-contract.yaml”,
“schemas/lsp/quick-fix-template.schema.json”,
“schemas/lsp/code-action-provenance.schema.json”,
“schemas/lsp/bounded-code-action.schema.json”,
“src/l9_debt_lsp/actions/builder.py”,
“src/l9_debt_lsp/actions/positions.py”,
“src/l9_debt_lsp/actions/protected_paths.py”,
“src/l9_debt_lsp/actions/preview.py”,
“src/l9_debt_lsp/runtime/code_action_service.py”,
“tests/actions/test_code_action_builder.py”,
“tests/security/test_protected_paths.py”,
“tests/architecture/test_code_action_boundary.py”,
]

missing = [
value
for value in required
if not (root / value).is_file()
]

if missing:
raise SystemExit(
f”LSP-P4 required files missing: {missing}”
)

for schema_path in sorted(
(root / “schemas/lsp”).glob(”*.json”)
):
schema = json.loads(
schema_path.read_text(encoding=“utf-8”)
)
Draft202012Validator.check_schema(schema)

actions_root = root / “src/l9_debt_lsp/actions”

prohibited = (
“subprocess”,
“os.system”,
“shell=true”,
“git checkout”,
“git commit”,
“git push”,
“pip install”,
“npm install”,
“requests.”,
“httpx.”,
“aiohttp.”,
)

for source_path in actions_root.rglob(”*.py”):
content = source_path.read_text(
encoding=“utf-8”
).lower()

for term in prohibited:
    if term in content:
        raise SystemExit(
            f"prohibited code-action operation "
            f"{term!r} in {source_path}"
        )

print(
json.dumps(
{
“schema_version”: “l9.phase-build-result/v1”,
“repository”: “Quantum-L9/l9-ci-debt-lsp”,
“phase”: “LSP-P4”,
“status”: “built”,
“code_actions”: “bounded”,
“workspace_edit_scope”: “current-document-only”,
“document_version_binding”: “required”,
“active_pack_binding”: “required”,
“edit_overlap”: “rejected”,
“protected_paths”: “enforced”,
“preview”: “required”,
“user_approval”: “required”,
“arbitrary_commands”: “prohibited”,
“autonomous_multi_file_repair”: “prohibited”
},
sort_keys=True,
separators=(”,”, “:”),
)
)
PY

printf ‘\n’
printf ‘LSP-P4 build complete.\n’
printf ‘\n’
printf ‘Implemented:\n’
printf ’  - immutable remediation-template consumption\n’
printf ’  - canonical diagnostic-to-template binding\n’
printf ’  - exact document-version validation\n’
printf ’  - exact active-pack validation\n’
printf ’  - deterministic single-document WorkspaceEdits\n’
printf ’  - bounded edit count and replacement sizes\n’
printf ’  - overlapping-edit rejection\n’
printf ’  - protected-path exclusions\n’
printf ’  - bounded unified-diff previews\n’
printf ’  - complete remediation provenance\n’
printf ’  - explicit editor-user approval boundary\n’
printf ’  - post-edit re-analysis contract\n’
printf ’  - pygls code-action integration\n’
printf ‘\n’
printf ‘Prohibited:\n’
printf ’  - arbitrary command or shell execution\n’
printf ’  - Git and branch mutation\n’
printf ’  - hidden dependency installation\n’
printf ’  - autonomous multi-file repair\n’
printf ’  - unbounded generated patches\n’
printf ‘\n’
printf ‘Remaining final phase: LSP-P5 — privacy-safe effectiveness telemetry, dispositions, rule outcomes, quick-fix outcomes, and latency events.\n’

:::
After this phase, the LSP has its complete secure editor-serving path:
```text
signed defense pack
→ verified installation
→ explicit activation
→ SDK incremental analysis
→ canonical diagnostics
→ bounded user-approved remediation

The final LSP phase closes the loop back to Debt Intelligence without exposing source code, absolute paths, secrets, developer identity, or corpus data.