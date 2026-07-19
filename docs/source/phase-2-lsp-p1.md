Phase 2 is LSP-P1: secure pack protocol, installation, activation, and rollback.

It aligns with the repository specification’s requirements for checksum validation, signature validation, atomic installation, explicit activation, previous-known-good retention, compatibility reporting, and rejection without replacing active state. repo-spec.yaml

Save as build-phase-2.sh and run it against the completed LSP-P0 repository.

#!/usr/bin/env bash
set -euo pipefail
###############################################################################
# Quantum-L9/l9-ci-debt-lsp
# LSP-P1 — Secure Pack Protocol
#
# Adds:
#   - publication-manifest validation
#   - SHA-256 archive verification
#   - Ed25519 detached-signature verification
#   - trusted-key policy
#   - safe deterministic archive extraction
#   - archive size and file-count limits
#   - content-addressed immutable installation
#   - quarantine for rejected artifacts
#   - explicit atomic activation
#   - previous-known-good retention
#   - rollback without recompilation
#   - retired-pack rejection
#   - startup state recovery and integrity verification
#   - compatibility reporting
#
# Does not yet add:
#   - SDK AnalysisSession integration
#   - document overlays
#   - diagnostics evaluation
#   - code actions
#   - telemetry transport
###############################################################################
fail() {
  printf 'LSP-P1: %s\n' "$*" >&2
  exit 1
}
require_file() {
  [[ -f "$1" ]] || fail "required LSP-P0 file missing: $1"
}
require_command() {
  command -v "$1" >/dev/null 2>&1 \
    || fail "required command not found: $1"
}
require_command python3
require_file ".l9/repo-spec.yaml"
require_file ".l9/defense-consumer-contract.yaml"
require_file ".l9/compatibility-policy.yaml"
require_file "schemas/lsp/pack-descriptor.schema.json"
require_file "src/l9_debt_lsp/contracts/compatibility.py"
require_file "src/l9_debt_lsp/runtime/capabilities.py"
require_file "pyproject.toml"
mkdir -p \
  .github/workflows \
  .l9 \
  docs/architecture/ADRs \
  schemas/lsp \
  src/l9_debt_lsp/packs \
  src/l9_debt_lsp/runtime \
  tests/packs \
  tests/runtime \
  tests/security \
  tests/fixtures/publication \
  tests/fixtures/trust
###############################################################################
# 1. Phase contract
###############################################################################
cat > .l9/pack-protocol-contract.yaml <<'EOF'
schema: l9.lsp-pack-protocol-contract/v1
metadata:
  repository: Quantum-L9/l9-ci-debt-lsp
  phase: LSP-P1
  status: authoritative
input:
  publication_manifest:
    protocol: l9.defense-publication/v1
    required: true
  archive:
    format: tar.gz
    required: true
  detached_signature:
    algorithm: Ed25519
    signed_value: archive_sha256
    required: true
  public_key:
    source: trusted-key-registry
    embedded_key_behavior: must_match_trusted_key
verification_order:
  - parse_manifest
  - validate_manifest_schema
  - validate_manifest_semantics
  - validate_trusted_signer
  - calculate_archive_sha256
  - compare_archive_sha256
  - verify_detached_signature
  - inspect_archive_limits
  - reject_unsafe_archive_paths
  - extract_to_private_staging_directory
  - validate_required_archive_members
  - validate_checksums_document
  - verify_member_checksums
  - validate_defense_pack_schema
  - validate_pack_identity_consistency
  - validate_compatibility
  - validate_retirement_state
  - atomically_install_content_addressed_pack
trust:
  registry: state/trust/trusted-keys.json
  default_behavior: reject_unknown_signer
  key_identity:
    algorithm: SHA-256
    input: raw_Ed25519_public_key
    prefix: key_
  requirements:
    - key enabled
    - key algorithm is Ed25519
    - key usage includes defense-pack-verification
    - manifest signer identity matches trusted key identity
    - embedded public key matches trusted registry key
  prohibited:
    - trust on first use
    - implicit key enrollment
    - private keys in repository
    - private keys in runtime state
    - accepting disabled keys
    - accepting unknown keys
archive_limits:
  maximum_archive_bytes: 52428800
  maximum_uncompressed_bytes: 209715200
  maximum_member_count: 10000
  maximum_single_member_bytes: 52428800
  maximum_path_length: 512
  maximum_path_depth: 20
archive_security:
  prohibited_members:
    - symbolic_links
    - hard_links
    - devices
    - fifos
    - sockets
    - absolute_paths
    - parent_directory_traversal
    - duplicate_paths
    - case_folded_duplicate_paths
  extraction:
    destination: private_staging_directory
    file_mode: "0644"
    directory_mode: "0755"
    preserve_archive_ownership: false
    preserve_archive_permissions: false
    preserve_archive_timestamps: false
installation:
  root: state/packs
  identity: pack_id
  immutable: true
  required_state:
    - manifest.json
    - defense-pack.json
    - compatibility.json
    - checksums.json
    - installation.json
    - archive.sha256
  duplicate_behavior:
    same_content: idempotent_success
    different_content_same_pack_id: reject_identity_collision
  atomicity:
    staging_directory: required
    fsync_files: required
    fsync_directories: required
    final_operation: atomic_rename
activation:
  separate_from_installation: true
  explicit_pack_id_required: true
  state_root: state/activation
  active_pointer: active.json
  previous_pointer: previous-known-good.json
  history: activation-history.jsonl
  atomicity:
    temporary_file_same_filesystem: required
    fsync_file: required
    atomic_replace: required
    fsync_parent_directory: required
  preconditions:
    - pack installed
    - pack integrity valid
    - pack compatible
    - pack not retired
  failure_behavior: preserve_current_active_state
rollback:
  target: previous-known-good
  recompilation: prohibited
  network_dependency: prohibited
  preconditions:
    - previous-known-good exists
    - previous-known-good pack integrity valid
    - previous-known-good pack compatible
    - previous-known-good pack not retired
  behavior:
    - atomically activate previous-known-good
    - move former active pack into previous-known-good
    - append activation history
  failure_behavior: preserve_current_active_state
retirement:
  state_file: state/retirement/retired-packs.json
  append_only_semantics: required
  activation_behavior: reject
  installed_pack_behavior: retain_for_audit
  active_pack_behavior:
    - report_retired_active_state
    - do_not_silently_switch
    - require_explicit_rollback_or_activation
quarantine:
  root: state/quarantine
  identity:
    algorithm: SHA-256
    inputs:
      - archive_sha256
      - manifest_sha256
      - reason_code
  contents:
    - rejection.json
    - publication-manifest.json
    - archive-reference.json
  archive_copy:
    default: false
    reason: avoid duplicating untrusted large artifacts
  required_reasons:
    - malformed_manifest
    - unsupported_manifest_protocol
    - archive_too_large
    - archive_hash_mismatch
    - unknown_signer
    - disabled_signer
    - signer_key_mismatch
    - signature_invalid
    - unsafe_archive
    - required_member_missing
    - member_checksum_mismatch
    - invalid_defense_pack
    - pack_identity_mismatch
    - incompatible_pack
    - retired_pack
    - immutable_identity_collision
runtime_state:
  root_environment_variable: L9_DEBT_LSP_STATE_ROOT
  default:
    linux: ~/.local/state/l9/debt-lsp
    macOS: ~/Library/Application Support/L9/debt-lsp
    windows: "%LOCALAPPDATA%/L9/debt-lsp"
  permissions:
    directories: owner_read_write_execute
    files: owner_read_write
  sensitive_content:
    private_keys: prohibited
    source_content: prohibited
    raw_logs: prohibited
    absolute_workspace_paths: prohibited
phase:
  id: LSP-P1
  status: implemented
  includes:
    - trusted-key registry
    - manifest validation
    - archive hash verification
    - Ed25519 verification
    - safe extraction
    - immutable installation
    - compatibility rejection
    - retired-pack rejection
    - explicit activation
    - previous-known-good retention
    - rollback
    - startup recovery
    - quarantine metadata
  excludes:
    - network pack discovery
    - automatic update
    - SDK AnalysisSession
    - diagnostics
    - code actions
    - telemetry transport
EOF
###############################################################################
# 2. Schemas
###############################################################################
cat > schemas/lsp/trusted-key-registry.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/trusted-key-registry/v1",
  "title": "L9 LSP Trusted Key Registry",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "keys"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.trusted-key-registry/v1"
    },
    "keys": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/key"
      }
    }
  },
  "$defs": {
    "key": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "key_id",
        "algorithm",
        "public_key",
        "enabled",
        "usages",
        "issuer",
        "limitations"
      ],
      "properties": {
        "key_id": {
          "type": "string",
          "pattern": "^key_[0-9a-f]{64}$"
        },
        "algorithm": {
          "const": "Ed25519"
        },
        "public_key": {
          "type": "string",
          "minLength": 40
        },
        "enabled": {
          "type": "boolean"
        },
        "usages": {
          "type": "array",
          "items": {
            "enum": [
              "defense-pack-verification"
            ]
          },
          "contains": {
            "const": "defense-pack-verification"
          },
          "uniqueItems": true
        },
        "issuer": {
          "type": "string",
          "minLength": 1
        },
        "not_before": {
          "type": [
            "string",
            "null"
          ],
          "format": "date-time"
        },
        "not_after": {
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
  }
}
EOF
cat > schemas/lsp/publication-manifest.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/publication-manifest/v1",
  "title": "L9 Defense Publication Manifest Consumer Schema",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "pack_id",
    "pack_version",
    "archive_name",
    "archive_sha256",
    "archive_size",
    "signature",
    "public_key",
    "signer_key_id",
    "signature_algorithm",
    "channel",
    "rollback",
    "publication_gates"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.defense-publication/v1"
    },
    "pack_id": {
      "type": "string",
      "pattern": "^pack_[0-9a-f]{64}$"
    },
    "pack_version": {
      "type": "string",
      "minLength": 1
    },
    "archive_name": {
      "type": "string",
      "pattern": "^[A-Za-z0-9._-]+\\.tar\\.gz$"
    },
    "archive_sha256": {
      "type": "string",
      "pattern": "^[0-9a-f]{64}$"
    },
    "archive_size": {
      "type": "integer",
      "minimum": 1,
      "maximum": 52428800
    },
    "signature": {
      "type": "string",
      "minLength": 40
    },
    "public_key": {
      "type": "string",
      "minLength": 40
    },
    "signer_key_id": {
      "type": "string",
      "pattern": "^key_[0-9a-f]{64}$"
    },
    "signature_algorithm": {
      "const": "Ed25519"
    },
    "channel": {
      "enum": [
        "experimental",
        "shadow",
        "stable"
      ]
    },
    "rollback": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "available",
        "previous_pack_version",
        "previous_pack_sha256"
      ],
      "properties": {
        "available": {
          "type": "boolean"
        },
        "previous_pack_version": {
          "type": [
            "string",
            "null"
          ]
        },
        "previous_pack_sha256": {
          "type": [
            "string",
            "null"
          ],
          "pattern": "^[0-9a-f]{64}$"
        }
      }
    },
    "publication_gates": {
      "type": "object",
      "minProperties": 1,
      "additionalProperties": {
        "const": true
      }
    }
  }
}
EOF
cat > schemas/lsp/installation-record.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/installation-record/v1",
  "title": "L9 LSP Immutable Pack Installation Record",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "pack_id",
    "pack_version",
    "archive_sha256",
    "manifest_sha256",
    "signer_key_id",
    "compatibility_state",
    "installed_at",
    "content_hashes",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.pack-installation-record/v1"
    },
    "pack_id": {
      "type": "string",
      "pattern": "^pack_[0-9a-f]{64}$"
    },
    "pack_version": {
      "type": "string"
    },
    "archive_sha256": {
      "type": "string",
      "pattern": "^[0-9a-f]{64}$"
    },
    "manifest_sha256": {
      "type": "string",
      "pattern": "^[0-9a-f]{64}$"
    },
    "signer_key_id": {
      "type": "string",
      "pattern": "^key_[0-9a-f]{64}$"
    },
    "compatibility_state": {
      "const": "compatible"
    },
    "installed_at": {
      "type": "string",
      "format": "date-time"
    },
    "content_hashes": {
      "type": "object",
      "additionalProperties": {
        "type": "string",
        "pattern": "^[0-9a-f]{64}$"
      }
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
cat > schemas/lsp/activation-pointer.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/activation-pointer/v1",
  "title": "L9 LSP Active Pack Pointer",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "pack_id",
    "pack_version",
    "archive_sha256",
    "corpus_snapshot",
    "compiler_version",
    "taxonomy_version",
    "sdk_contract_version",
    "activated_at",
    "activation_id"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.pack-activation-pointer/v1"
    },
    "pack_id": {
      "type": "string",
      "pattern": "^pack_[0-9a-f]{64}$"
    },
    "pack_version": {
      "type": "string"
    },
    "archive_sha256": {
      "type": "string",
      "pattern": "^[0-9a-f]{64}$"
    },
    "corpus_snapshot": {
      "type": "string",
      "pattern": "^cs_[0-9a-f]{64}$"
    },
    "compiler_version": {
      "type": "string"
    },
    "taxonomy_version": {
      "type": "string"
    },
    "sdk_contract_version": {
      "type": "string"
    },
    "activated_at": {
      "type": "string",
      "format": "date-time"
    },
    "activation_id": {
      "type": "string",
      "pattern": "^activation_[0-9a-f]{64}$"
    }
  }
}
EOF
cat > schemas/lsp/activation-history-entry.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/activation-history-entry/v1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "sequence",
    "operation",
    "activation_id",
    "target_pack_id",
    "previous_pack_id",
    "occurred_at",
    "status",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.pack-activation-history-entry/v1"
    },
    "sequence": {
      "type": "integer",
      "minimum": 1
    },
    "operation": {
      "enum": [
        "activate",
        "rollback",
        "recovery"
      ]
    },
    "activation_id": {
      "type": "string",
      "pattern": "^activation_[0-9a-f]{64}$"
    },
    "target_pack_id": {
      "type": "string"
    },
    "previous_pack_id": {
      "type": [
        "string",
        "null"
      ]
    },
    "occurred_at": {
      "type": "string",
      "format": "date-time"
    },
    "status": {
      "enum": [
        "succeeded",
        "failed"
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
cat > schemas/lsp/retired-pack-registry.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/retired-pack-registry/v1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "retired"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.retired-pack-registry/v1"
    },
    "retired": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "pack_id",
          "pack_version",
          "reason",
          "retired_at",
          "issuer"
        ],
        "properties": {
          "pack_id": {
            "type": "string",
            "pattern": "^pack_[0-9a-f]{64}$"
          },
          "pack_version": {
            "type": "string"
          },
          "reason": {
            "type": "string"
          },
          "retired_at": {
            "type": "string",
            "format": "date-time"
          },
          "issuer": {
            "type": "string"
          }
        }
      }
    }
  }
}
EOF
cat > schemas/lsp/quarantine-record.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/quarantine-record/v1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "quarantine_id",
    "reason_code",
    "reason",
    "archive_sha256",
    "manifest_sha256",
    "observed_at",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.pack-quarantine-record/v1"
    },
    "quarantine_id": {
      "type": "string",
      "pattern": "^quarantine_[0-9a-f]{64}$"
    },
    "reason_code": {
      "type": "string"
    },
    "reason": {
      "type": "string"
    },
    "archive_sha256": {
      "type": [
        "string",
        "null"
      ],
      "pattern": "^[0-9a-f]{64}$"
    },
    "manifest_sha256": {
      "type": [
        "string",
        "null"
      ],
      "pattern": "^[0-9a-f]{64}$"
    },
    "observed_at": {
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
###############################################################################
# 3. Dependencies
###############################################################################
python3 - <<'PY'
from pathlib import Path
path = Path("pyproject.toml")
text = path.read_text(encoding="utf-8")
if '"cryptography>=43,<46"' not in text:
    text = text.replace(
        '  "pygls>=1.3,<2"\n]',
        '  "pygls>=1.3,<2",\n'
        '  "cryptography>=43,<46"\n'
        ']',
    )
path.write_text(text, encoding="utf-8")
PY
###############################################################################
# 4. Pack module
###############################################################################
cat > src/l9_debt_lsp/packs/__init__.py <<'EOF'
"""Secure installation and activation of immutable defense packs."""
EOF
cat > src/l9_debt_lsp/packs/errors.py <<'EOF'
from __future__ import annotations
class PackError(RuntimeError):
    """Base pack lifecycle failure."""
class ManifestValidationError(PackError):
    """The publication manifest is invalid."""
class TrustError(PackError):
    """The pack signer is not trusted."""
class SignatureError(PackError):
    """The pack signature is invalid."""
class ArchiveSecurityError(PackError):
    """The archive violates extraction security policy."""
class ArchiveIntegrityError(PackError):
    """The archive or one of its members failed integrity validation."""
class PackValidationError(PackError):
    """The extracted defense pack is invalid."""
class PackCompatibilityFailure(PackError):
    """The defense pack is incompatible with this runtime."""
class PackRetiredError(PackError):
    """The requested defense pack has been retired."""
class ImmutablePackCollisionError(PackError):
    """An existing pack identity contains different immutable content."""
class ActivationError(PackError):
    """Pack activation could not be completed atomically."""
class RollbackError(PackError):
    """Previous-known-good rollback could not be completed."""
EOF
cat > src/l9_debt_lsp/packs/models.py <<'EOF'
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
@dataclass(frozen=True)
class TrustedKey:
    key_id: str
    algorithm: str
    public_key: str
    enabled: bool
    usages: tuple[str, ...]
    issuer: str
    not_before: str | None
    not_after: str | None
    limitations: tuple[str, ...]
@dataclass(frozen=True)
class InstalledPack:
    pack_id: str
    pack_version: str
    path: Path
    archive_sha256: str
    manifest_sha256: str
    signer_key_id: str
    corpus_snapshot: str
    compiler_version: str
    taxonomy_version: str
    sdk_contract_version: str
    limitations: tuple[str, ...]
    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.pack-installation-result/v1",
            "status": "installed",
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "path": self.path.as_posix(),
            "archive_sha256": self.archive_sha256,
            "manifest_sha256": self.manifest_sha256,
            "signer_key_id": self.signer_key_id,
            "corpus_snapshot": self.corpus_snapshot,
            "compiler_version": self.compiler_version,
            "taxonomy_version": self.taxonomy_version,
            "sdk_contract_version": self.sdk_contract_version,
            "limitations": list(self.limitations),
        }
@dataclass(frozen=True)
class ActivationPointer:
    pack_id: str
    pack_version: str
    archive_sha256: str
    corpus_snapshot: str
    compiler_version: str
    taxonomy_version: str
    sdk_contract_version: str
    activated_at: str
    activation_id: str
    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.pack-activation-pointer/v1",
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "archive_sha256": self.archive_sha256,
            "corpus_snapshot": self.corpus_snapshot,
            "compiler_version": self.compiler_version,
            "taxonomy_version": self.taxonomy_version,
            "sdk_contract_version": self.sdk_contract_version,
            "activated_at": self.activated_at,
            "activation_id": self.activation_id,
        }
EOF
cat > src/l9_debt_lsp/packs/hashing.py <<'EOF'
from __future__ import annotations
import hashlib
from pathlib import Path
from typing import BinaryIO
from l9_debt_lsp.contracts.canonical import canonical_json
def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        _update_digest(stream, digest)
    return digest.hexdigest()
def _update_digest(
    stream: BinaryIO,
    digest: "hashlib._Hash",
) -> None:
    while True:
        block = stream.read(1024 * 1024)
        if not block:
            return
        digest.update(block)
def namespaced_hash(prefix: str, value: object) -> str:
    return prefix + sha256_bytes(canonical_json(value))
EOF
cat > src/l9_debt_lsp/packs/time.py <<'EOF'
from __future__ import annotations
import datetime as dt
def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)
def format_utc(value: dt.datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("time value must be timezone-aware")
    return (
        value.astimezone(dt.timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )
def parse_utc(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(
        value.replace("Z", "+00:00")
    ).astimezone(dt.timezone.utc)
EOF
cat > src/l9_debt_lsp/packs/jsonio.py <<'EOF'
from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path
from typing import Any
from l9_debt_lsp.contracts.canonical import canonical_json
def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value
def write_canonical_json(
    path: Path,
    value: object,
    *,
    mode: int = 0o600,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = canonical_json(value) + b"\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)
def append_canonical_jsonl(
    path: Path,
    value: object,
    *,
    mode: int = 0o600,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        path,
        os.O_APPEND | os.O_CREAT | os.O_WRONLY,
        mode,
    )
    try:
        with os.fdopen(descriptor, "ab") as stream:
            stream.write(canonical_json(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        fsync_directory(path.parent)
def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
EOF
cat > src/l9_debt_lsp/packs/paths.py <<'EOF'
from __future__ import annotations
import os
import platform
from dataclasses import dataclass
from pathlib import Path
def default_state_root() -> Path:
    override = os.environ.get("L9_DEBT_LSP_STATE_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    system = platform.system().lower()
    if system == "windows":
        base = os.environ.get("LOCALAPPDATA")
        if not base:
            base = str(Path.home() / "AppData/Local")
        return (Path(base) / "L9/debt-lsp").resolve()
    if system == "darwin":
        return (
            Path.home()
            / "Library/Application Support/L9/debt-lsp"
        ).resolve()
    xdg_state = os.environ.get("XDG_STATE_HOME")
    if xdg_state:
        return (Path(xdg_state) / "l9/debt-lsp").resolve()
    return (
        Path.home() / ".local/state/l9/debt-lsp"
    ).resolve()
@dataclass(frozen=True)
class StatePaths:
    root: Path
    @property
    def packs(self) -> Path:
        return self.root / "packs"
    @property
    def staging(self) -> Path:
        return self.root / "staging"
    @property
    def quarantine(self) -> Path:
        return self.root / "quarantine"
    @property
    def trust(self) -> Path:
        return self.root / "trust"
    @property
    def trusted_keys(self) -> Path:
        return self.trust / "trusted-keys.json"
    @property
    def activation(self) -> Path:
        return self.root / "activation"
    @property
    def active(self) -> Path:
        return self.activation / "active.json"
    @property
    def previous(self) -> Path:
        return self.activation / "previous-known-good.json"
    @property
    def activation_history(self) -> Path:
        return self.activation / "activation-history.jsonl"
    @property
    def retirement(self) -> Path:
        return self.root / "retirement"
    @property
    def retired_packs(self) -> Path:
        return self.retirement / "retired-packs.json"
    def initialize(self) -> None:
        for directory in (
            self.root,
            self.packs,
            self.staging,
            self.quarantine,
            self.trust,
            self.activation,
            self.retirement,
        ):
            directory.mkdir(parents=True, exist_ok=True)
            directory.chmod(0o700)
EOF
cat > src/l9_debt_lsp/packs/trust.py <<'EOF'
from __future__ import annotations
import base64
import datetime as dt
from pathlib import Path
from typing import Any
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
)
from l9_debt_lsp.contracts.schema import SchemaValidator
from .errors import TrustError
from .hashing import namespaced_hash
from .jsonio import load_json
from .models import TrustedKey
from .time import parse_utc, utc_now
KEY_USAGE = "defense-pack-verification"
def public_key_id(public_key_base64: str) -> str:
    try:
        raw = base64.b64decode(
            public_key_base64.encode("ascii"),
            validate=True,
        )
    except Exception as error:
        raise TrustError("public key is not valid base64") from error
    if len(raw) != 32:
        raise TrustError("Ed25519 public key must be 32 bytes")
    return namespaced_hash("key_", {"raw_public_key": raw.hex()})
class TrustRegistry:
    def __init__(
        self,
        registry_path: Path,
        schema_path: Path,
    ) -> None:
        self.registry_path = registry_path
        self.schema_path = schema_path
    def load(self) -> dict[str, TrustedKey]:
        if not self.registry_path.is_file():
            raise TrustError(
                f"trusted key registry does not exist: "
                f"{self.registry_path}"
            )
        document = load_json(self.registry_path)
        SchemaValidator(self.schema_path).validate(document)
        keys: dict[str, TrustedKey] = {}
        for entry in document["keys"]:
            key = TrustedKey(
                key_id=entry["key_id"],
                algorithm=entry["algorithm"],
                public_key=entry["public_key"],
                enabled=entry["enabled"],
                usages=tuple(sorted(entry["usages"])),
                issuer=entry["issuer"],
                not_before=entry.get("not_before"),
                not_after=entry.get("not_after"),
                limitations=tuple(
                    sorted(set(entry.get("limitations", [])))
                ),
            )
            calculated = public_key_id(key.public_key)
            if key.key_id != calculated:
                raise TrustError(
                    f"trusted key identity mismatch: {key.key_id}"
                )
            if key.key_id in keys:
                raise TrustError(
                    f"duplicate trusted key identity: {key.key_id}"
                )
            keys[key.key_id] = key
        return keys
    def require_verification_key(
        self,
        *,
        key_id: str,
        embedded_public_key: str,
        now: dt.datetime | None = None,
    ) -> TrustedKey:
        now = now or utc_now()
        keys = self.load()
        key = keys.get(key_id)
        if key is None:
            raise TrustError(f"unknown signer key: {key_id}")
        if not key.enabled:
            raise TrustError(f"signer key is disabled: {key_id}")
        if key.algorithm != "Ed25519":
            raise TrustError(
                f"unsupported signer algorithm: {key.algorithm}"
            )
        if KEY_USAGE not in key.usages:
            raise TrustError(
                f"signer key lacks required usage: {KEY_USAGE}"
            )
        if key.public_key != embedded_public_key:
            raise TrustError(
                "manifest public key does not match trusted key"
            )
        if key.not_before is not None:
            if now < parse_utc(key.not_before):
                raise TrustError(
                    f"signer key is not yet valid: {key_id}"
                )
        if key.not_after is not None:
            if now >= parse_utc(key.not_after):
                raise TrustError(
                    f"signer key has expired: {key_id}"
                )
        try:
            raw = base64.b64decode(
                key.public_key.encode("ascii"),
                validate=True,
            )
            Ed25519PublicKey.from_public_bytes(raw)
        except Exception as error:
            raise TrustError(
                f"trusted key is not valid Ed25519: {key_id}"
            ) from error
        return key
EOF
cat > src/l9_debt_lsp/packs/signature.py <<'EOF'
from __future__ import annotations
import base64
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
)
from .errors import SignatureError
def verify_archive_digest(
    *,
    archive_sha256: str,
    signature_base64: str,
    public_key_base64: str,
) -> None:
    try:
        digest = bytes.fromhex(archive_sha256)
    except ValueError as error:
        raise SignatureError(
            "archive digest is not valid hexadecimal"
        ) from error
    try:
        signature = base64.b64decode(
            signature_base64.encode("ascii"),
            validate=True,
        )
        public_key = base64.b64decode(
            public_key_base64.encode("ascii"),
            validate=True,
        )
    except Exception as error:
        raise SignatureError(
            "signature or public key is not valid base64"
        ) from error
    if len(public_key) != 32:
        raise SignatureError(
            "Ed25519 public key must be 32 bytes"
        )
    try:
        Ed25519PublicKey.from_public_bytes(
            public_key
        ).verify(signature, digest)
    except InvalidSignature as error:
        raise SignatureError(
            "defense-pack signature verification failed"
        ) from error
    except Exception as error:
        raise SignatureError(
            "unable to verify defense-pack signature"
        ) from error
EOF
cat > src/l9_debt_lsp/packs/archive.py <<'EOF'
from __future__ import annotations
import os
import shutil
import tarfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from .errors import ArchiveSecurityError
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024
MAX_MEMBER_COUNT = 10_000
MAX_SINGLE_MEMBER_BYTES = 50 * 1024 * 1024
MAX_PATH_LENGTH = 512
MAX_PATH_DEPTH = 20
@dataclass(frozen=True)
class ArchiveInspection:
    member_count: int
    uncompressed_bytes: int
    file_paths: tuple[str, ...]
def _validate_member_name(name: str) -> PurePosixPath:
    if not name:
        raise ArchiveSecurityError(
            "archive contains an empty member name"
        )
    if len(name) > MAX_PATH_LENGTH:
        raise ArchiveSecurityError(
            f"archive member path exceeds limit: {name!r}"
        )
    path = PurePosixPath(name)
    if path.is_absolute():
        raise ArchiveSecurityError(
            f"absolute archive path is prohibited: {name!r}"
        )
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ArchiveSecurityError(
            f"unsafe archive member path: {name!r}"
        )
    if len(path.parts) > MAX_PATH_DEPTH:
        raise ArchiveSecurityError(
            f"archive path depth exceeds limit: {name!r}"
        )
    return path
def inspect_archive(path: Path) -> ArchiveInspection:
    archive_size = path.stat().st_size
    if archive_size > MAX_ARCHIVE_BYTES:
        raise ArchiveSecurityError(
            f"archive exceeds {MAX_ARCHIVE_BYTES} bytes"
        )
    member_count = 0
    uncompressed_bytes = 0
    exact_names: set[str] = set()
    folded_names: set[str] = set()
    file_paths: list[str] = []
    try:
        archive = tarfile.open(path, mode="r:gz")
    except tarfile.TarError as error:
        raise ArchiveSecurityError(
            "archive is not a valid tar.gz file"
        ) from error
    with archive:
        for member in archive:
            member_count += 1
            if member_count > MAX_MEMBER_COUNT:
                raise ArchiveSecurityError(
                    "archive member count exceeds limit"
                )
            normalized = _validate_member_name(member.name)
            normalized_name = normalized.as_posix()
            folded = normalized_name.casefold()
            if normalized_name in exact_names:
                raise ArchiveSecurityError(
                    f"duplicate archive path: {normalized_name}"
                )
            if folded in folded_names:
                raise ArchiveSecurityError(
                    "case-folded duplicate archive path: "
                    f"{normalized_name}"
                )
            exact_names.add(normalized_name)
            folded_names.add(folded)
            if (
                member.issym()
                or member.islnk()
                or member.isdev()
                or member.isfifo()
            ):
                raise ArchiveSecurityError(
                    f"unsupported archive member type: "
                    f"{normalized_name}"
                )
            if not (member.isfile() or member.isdir()):
                raise ArchiveSecurityError(
                    f"unsupported archive member: {normalized_name}"
                )
            if member.size < 0:
                raise ArchiveSecurityError(
                    f"negative archive member size: {normalized_name}"
                )
            if member.size > MAX_SINGLE_MEMBER_BYTES:
                raise ArchiveSecurityError(
                    f"archive member exceeds size limit: "
                    f"{normalized_name}"
                )
            uncompressed_bytes += member.size
            if uncompressed_bytes > MAX_UNCOMPRESSED_BYTES:
                raise ArchiveSecurityError(
                    "archive uncompressed size exceeds limit"
                )
            if member.isfile():
                file_paths.append(normalized_name)
    return ArchiveInspection(
        member_count=member_count,
        uncompressed_bytes=uncompressed_bytes,
        file_paths=tuple(sorted(file_paths)),
    )
def extract_archive_safely(
    archive_path: Path,
    destination: Path,
) -> ArchiveInspection:
    inspection = inspect_archive(archive_path)
    if destination.exists():
        raise ArchiveSecurityError(
            f"staging destination already exists: {destination}"
        )
    destination.mkdir(parents=True, mode=0o700)
    destination_root = destination.resolve()
    try:
        with tarfile.open(archive_path, mode="r:gz") as archive:
            for member in archive:
                relative = _validate_member_name(member.name)
                target = (destination / relative).resolve()
                if (
                    target != destination_root
                    and destination_root not in target.parents
                ):
                    raise ArchiveSecurityError(
                        f"archive member escapes destination: "
                        f"{member.name}"
                    )
                if member.isdir():
                    target.mkdir(
                        parents=True,
                        exist_ok=True,
                        mode=0o755,
                    )
                    continue
                target.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                    mode=0o755,
                )
                source = archive.extractfile(member)
                if source is None:
                    raise ArchiveSecurityError(
                        f"unable to read archive member: "
                        f"{member.name}"
                    )
                descriptor = os.open(
                    target,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o644,
                )
                try:
                    with os.fdopen(descriptor, "wb") as output:
                        shutil.copyfileobj(
                            source,
                            output,
                            length=1024 * 1024,
                        )
                        output.flush()
                        os.fsync(output.fileno())
                finally:
                    source.close()
        return inspection
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
EOF
cat > src/l9_debt_lsp/packs/manifest.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from typing import Any
from l9_debt_lsp.contracts.schema import SchemaValidator
from .errors import ManifestValidationError
from .hashing import sha256_file
from .jsonio import load_json
def load_and_validate_manifest(
    *,
    manifest_path: Path,
    schema_path: Path,
) -> dict[str, Any]:
    try:
        manifest = load_json(manifest_path)
        SchemaValidator(schema_path).validate(manifest)
    except Exception as error:
        raise ManifestValidationError(
            f"publication manifest validation failed: {error}"
        ) from error
    if manifest["signature_algorithm"] != "Ed25519":
        raise ManifestValidationError(
            "only Ed25519 signatures are supported"
        )
    if not all(manifest["publication_gates"].values()):
        raise ManifestValidationError(
            "publication manifest contains an unpassed gate"
        )
    return manifest
def verify_archive_reference(
    *,
    manifest: dict[str, Any],
    archive_path: Path,
) -> str:
    actual_size = archive_path.stat().st_size
    if actual_size != manifest["archive_size"]:
        raise ManifestValidationError(
            "archive size does not match publication manifest"
        )
    actual_hash = sha256_file(archive_path)
    if actual_hash != manifest["archive_sha256"]:
        raise ManifestValidationError(
            "archive SHA-256 does not match publication manifest"
        )
    return actual_hash
EOF
cat > src/l9_debt_lsp/packs/contents.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from typing import Any
from l9_debt_lsp.contracts.schema import SchemaValidator
from .errors import ArchiveIntegrityError, PackValidationError
from .hashing import sha256_file
from .jsonio import load_json
REQUIRED_MEMBERS = (
    "defense-pack.json",
    "compatibility.json",
    "checksums.json",
)
def validate_required_members(root: Path) -> None:
    missing = [
        name for name in REQUIRED_MEMBERS
        if not (root / name).is_file()
    ]
    if missing:
        raise ArchiveIntegrityError(
            f"required archive members are missing: {missing}"
        )
def load_checksums(root: Path) -> dict[str, str]:
    document = load_json(root / "checksums.json")
    checksums = document.get("checksums", document)
    if not isinstance(checksums, dict):
        raise ArchiveIntegrityError(
            "checksums document must contain an object"
        )
    result: dict[str, str] = {}
    for name, digest in checksums.items():
        if not isinstance(name, str):
            raise ArchiveIntegrityError(
                "checksum path must be a string"
            )
        if not isinstance(digest, str):
            raise ArchiveIntegrityError(
                f"checksum value must be a string: {name}"
            )
        if len(digest) != 64:
            raise ArchiveIntegrityError(
                f"checksum must be SHA-256: {name}"
            )
        result[name] = digest
    return dict(sorted(result.items()))
def verify_member_checksums(
    root: Path,
    checksums: dict[str, str],
) -> dict[str, str]:
    verified: dict[str, str] = {}
    for relative_name, expected in checksums.items():
        relative = Path(relative_name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ArchiveIntegrityError(
                f"unsafe checksum path: {relative_name}"
            )
        path = root / relative
        if not path.is_file():
            raise ArchiveIntegrityError(
                f"checksummed member is missing: {relative_name}"
            )
        actual = sha256_file(path)
        if actual != expected:
            raise ArchiveIntegrityError(
                f"member checksum mismatch: {relative_name}"
            )
        verified[relative_name] = actual
    return verified
def load_and_validate_defense_pack(
    *,
    root: Path,
    schema_path: Path,
) -> dict[str, Any]:
    defense_pack = load_json(root / "defense-pack.json")
    try:
        SchemaValidator(schema_path).validate(defense_pack)
    except Exception as error:
        raise PackValidationError(
            f"defense-pack schema validation failed: {error}"
        ) from error
    return defense_pack
def validate_identity_consistency(
    *,
    manifest: dict[str, Any],
    defense_pack: dict[str, Any],
) -> None:
    if manifest["pack_id"] != defense_pack["pack_id"]:
        raise PackValidationError(
            "manifest and defense pack use different pack IDs"
        )
    if manifest["pack_version"] != defense_pack["version"]:
        raise PackValidationError(
            "manifest and defense pack use different versions"
        )
    compatibility = load_json(
        Path(defense_pack.get(
            "__compatibility_path__",
            "compatibility.json",
        ))
    ) if False else None
    del compatibility
EOF
cat > src/l9_debt_lsp/packs/retirement.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from typing import Any
from l9_debt_lsp.contracts.schema import SchemaValidator
from .errors import PackRetiredError
from .jsonio import load_json, write_canonical_json
EMPTY_REGISTRY = {
    "schema_version": "l9.retired-pack-registry/v1",
    "retired": [],
}
class RetirementRegistry:
    def __init__(
        self,
        path: Path,
        schema_path: Path,
    ) -> None:
        self.path = path
        self.schema_path = schema_path
    def initialize(self) -> None:
        if not self.path.exists():
            write_canonical_json(
                self.path,
                EMPTY_REGISTRY,
            )
    def load(self) -> dict[str, Any]:
        self.initialize()
        document = load_json(self.path)
        SchemaValidator(self.schema_path).validate(document)
        return document
    def require_not_retired(
        self,
        *,
        pack_id: str,
        pack_version: str,
    ) -> None:
        document = self.load()
        for entry in document["retired"]:
            if (
                entry["pack_id"] == pack_id
                or (
                    entry["pack_version"] == pack_version
                    and entry["pack_id"] == pack_id
                )
            ):
                raise PackRetiredError(
                    f"defense pack is retired: "
                    f"{pack_id} ({pack_version})"
                )
EOF
cat > src/l9_debt_lsp/packs/quarantine.py <<'EOF'
from __future__ import annotations
from pathlib import Path
from typing import Any
from l9_debt_lsp.contracts.canonical import canonical_json
from .hashing import namespaced_hash, sha256_bytes, sha256_file
from .jsonio import write_canonical_json
from .time import format_utc, utc_now
class QuarantineStore:
    def __init__(self, root: Path) -> None:
        self.root = root
    def record(
        self,
        *,
        reason_code: str,
        reason: str,
        manifest_path: Path | None,
        archive_path: Path | None,
        limitations: list[str] | None = None,
    ) -> dict[str, Any]:
        manifest_hash = (
            sha256_file(manifest_path)
            if manifest_path is not None
            and manifest_path.is_file()
            else None
        )
        archive_hash = (
            sha256_file(archive_path)
            if archive_path is not None
            and archive_path.is_file()
            else None
        )
        identity = {
            "archive_sha256": archive_hash,
            "manifest_sha256": manifest_hash,
            "reason_code": reason_code,
        }
        quarantine_id = namespaced_hash(
            "quarantine_",
            identity,
        )
        destination = self.root / quarantine_id
        destination.mkdir(parents=True, exist_ok=True)
        destination.chmod(0o700)
        record = {
            "schema_version": "l9.pack-quarantine-record/v1",
            "quarantine_id": quarantine_id,
            "reason_code": reason_code,
            "reason": reason,
            "archive_sha256": archive_hash,
            "manifest_sha256": manifest_hash,
            "observed_at": format_utc(utc_now()),
            "limitations": sorted(
                set(limitations or [])
            ),
        }
        write_canonical_json(
            destination / "rejection.json",
            record,
        )
        if manifest_path is not None and manifest_path.is_file():
            manifest_bytes = manifest_path.read_bytes()
            write_canonical_json(
                destination / "publication-manifest-reference.json",
                {
                    "schema_version": (
                        "l9.quarantined-manifest-reference/v1"
                    ),
                    "sha256": sha256_bytes(manifest_bytes),
                    "size": len(manifest_bytes),
                    "source_name": manifest_path.name,
                },
            )
        if archive_path is not None and archive_path.is_file():
            write_canonical_json(
                destination / "archive-reference.json",
                {
                    "schema_version": (
                        "l9.quarantined-archive-reference/v1"
                    ),
                    "sha256": archive_hash,
                    "size": archive_path.stat().st_size,
                    "source_name": archive_path.name,
                },
            )
        return record
EOF
cat > src/l9_debt_lsp/packs/store.py <<'EOF'
from __future__ import annotations
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any
from l9_debt_lsp.contracts.canonical import canonical_json
from .errors import (
    ImmutablePackCollisionError,
    PackValidationError,
)
from .hashing import sha256_file
from .jsonio import (
    fsync_directory,
    load_json,
    write_canonical_json,
)
from .models import InstalledPack
from .time import format_utc, utc_now
REQUIRED_INSTALLED_FILES = (
    "manifest.json",
    "defense-pack.json",
    "compatibility.json",
    "checksums.json",
    "installation.json",
    "archive.sha256",
)
class PackStore:
    def __init__(
        self,
        *,
        packs_root: Path,
        staging_root: Path,
    ) -> None:
        self.packs_root = packs_root
        self.staging_root = staging_root
    def pack_path(self, pack_id: str) -> Path:
        return self.packs_root / pack_id
    def install(
        self,
        *,
        extracted_root: Path,
        manifest: dict[str, Any],
        defense_pack: dict[str, Any],
        manifest_path: Path,
        archive_sha256: str,
        signer_key_id: str,
        content_hashes: dict[str, str],
        limitations: list[str],
    ) -> InstalledPack:
        pack_id = defense_pack["pack_id"]
        destination = self.pack_path(pack_id)
        manifest_sha256 = sha256_file(manifest_path)
        if destination.exists():
            installed = self.load(pack_id)
            if (
                installed.archive_sha256 == archive_sha256
                and installed.manifest_sha256 == manifest_sha256
            ):
                return installed
            raise ImmutablePackCollisionError(
                f"pack identity collision: {pack_id}"
            )
        self.packs_root.mkdir(parents=True, exist_ok=True)
        self.staging_root.mkdir(parents=True, exist_ok=True)
        temporary = Path(
            tempfile.mkdtemp(
                prefix=f".install-{pack_id}.",
                dir=self.staging_root,
            )
        )
        temporary.chmod(0o700)
        try:
            shutil.copytree(
                extracted_root,
                temporary / "content",
                dirs_exist_ok=False,
            )
            content_root = temporary / "content"
            shutil.copy2(
                manifest_path,
                content_root / "manifest.json",
            )
            installation = {
                "schema_version": "l9.pack-installation-record/v1",
                "pack_id": pack_id,
                "pack_version": defense_pack["version"],
                "archive_sha256": archive_sha256,
                "manifest_sha256": manifest_sha256,
                "signer_key_id": signer_key_id,
                "compatibility_state": "compatible",
                "installed_at": format_utc(utc_now()),
                "content_hashes": dict(
                    sorted(content_hashes.items())
                ),
                "limitations": sorted(set(limitations)),
            }
            write_canonical_json(
                content_root / "installation.json",
                installation,
            )
            archive_hash_path = content_root / "archive.sha256"
            archive_hash_path.write_text(
                archive_sha256 + "\n",
                encoding="ascii",
            )
            archive_hash_path.chmod(0o600)
            self._fsync_tree(content_root)
            os.replace(content_root, destination)
            fsync_directory(self.packs_root)
            return self.load(pack_id)
        finally:
            shutil.rmtree(temporary, ignore_errors=True)
    def load(self, pack_id: str) -> InstalledPack:
        root = self.pack_path(pack_id)
        if not root.is_dir():
            raise PackValidationError(
                f"pack is not installed: {pack_id}"
            )
        missing = [
            name for name in REQUIRED_INSTALLED_FILES
            if not (root / name).is_file()
        ]
        if missing:
            raise PackValidationError(
                f"installed pack is incomplete: {missing}"
            )
        installation = load_json(root / "installation.json")
        defense_pack = load_json(root / "defense-pack.json")
        archive_sha256 = (
            root / "archive.sha256"
        ).read_text(encoding="ascii").strip()
        if installation["pack_id"] != pack_id:
            raise PackValidationError(
                "installation pack ID does not match directory"
            )
        if defense_pack["pack_id"] != pack_id:
            raise PackValidationError(
                "defense pack ID does not match directory"
            )
        if archive_sha256 != installation["archive_sha256"]:
            raise PackValidationError(
                "archive hash file does not match installation record"
            )
        return InstalledPack(
            pack_id=pack_id,
            pack_version=installation["pack_version"],
            path=root,
            archive_sha256=archive_sha256,
            manifest_sha256=installation["manifest_sha256"],
            signer_key_id=installation["signer_key_id"],
            corpus_snapshot=defense_pack["corpus_snapshot"],
            compiler_version=defense_pack["compiler_version"],
            taxonomy_version=defense_pack["taxonomy_version"],
            sdk_contract_version=defense_pack[
                "SDK_contract_version"
            ],
            limitations=tuple(
                sorted(set(installation["limitations"]))
            ),
        )
    def verify_integrity(
        self,
        pack_id: str,
    ) -> InstalledPack:
        installed = self.load(pack_id)
        installation = load_json(
            installed.path / "installation.json"
        )
        expected_hashes = installation["content_hashes"]
        for relative_name, expected_hash in expected_hashes.items():
            path = installed.path / relative_name
            if not path.is_file():
                raise PackValidationError(
                    f"installed pack member is missing: "
                    f"{relative_name}"
                )
            actual_hash = sha256_file(path)
            if actual_hash != expected_hash:
                raise PackValidationError(
                    f"installed pack member hash mismatch: "
                    f"{relative_name}"
                )
        return installed
    @staticmethod
    def _fsync_tree(root: Path) -> None:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                descriptor = os.open(path, os.O_RDONLY)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
        directories = sorted(
            (path for path in root.rglob("*") if path.is_dir()),
            key=lambda value: len(value.parts),
            reverse=True,
        )
        for directory in directories:
            fsync_directory(directory)
        fsync_directory(root)
EOF
cat > src/l9_debt_lsp/packs/installer.py <<'EOF'
from __future__ import annotations
import shutil
import tempfile
from pathlib import Path
from typing import Any
from l9_debt_lsp.contracts.compatibility import (
    evaluate_compatibility,
)
from l9_debt_lsp.contracts.descriptor import (
    descriptor_from_defense_pack,
)
from .archive import extract_archive_safely
from .contents import (
    load_and_validate_defense_pack,
    load_checksums,
    validate_identity_consistency,
    validate_required_members,
    verify_member_checksums,
)
from .errors import (
    PackCompatibilityFailure,
    PackError,
)
from .hashing import sha256_file
from .jsonio import load_json
from .manifest import (
    load_and_validate_manifest,
    verify_archive_reference,
)
from .models import InstalledPack
from .paths import StatePaths
from .quarantine import QuarantineStore
from .retirement import RetirementRegistry
from .signature import verify_archive_digest
from .store import PackStore
from .trust import TrustRegistry
class PackInstaller:
    def __init__(
        self,
        *,
        paths: StatePaths,
        schema_root: Path,
    ) -> None:
        self.paths = paths
        self.schema_root = schema_root
        self.trust = TrustRegistry(
            paths.trusted_keys,
            schema_root / "trusted-key-registry.schema.json",
        )
        self.retirement = RetirementRegistry(
            paths.retired_packs,
            schema_root / "retired-pack-registry.schema.json",
        )
        self.store = PackStore(
            packs_root=paths.packs,
            staging_root=paths.staging,
        )
        self.quarantine = QuarantineStore(paths.quarantine)
    def install(
        self,
        *,
        manifest_path: Path,
        archive_path: Path,
        platform_identity: str | None = None,
    ) -> InstalledPack:
        self.paths.initialize()
        try:
            manifest = load_and_validate_manifest(
                manifest_path=manifest_path,
                schema_path=(
                    self.schema_root
                    / "publication-manifest.schema.json"
                ),
            )
            archive_sha256 = verify_archive_reference(
                manifest=manifest,
                archive_path=archive_path,
            )
            trusted_key = self.trust.require_verification_key(
                key_id=manifest["signer_key_id"],
                embedded_public_key=manifest["public_key"],
            )
            verify_archive_digest(
                archive_sha256=archive_sha256,
                signature_base64=manifest["signature"],
                public_key_base64=trusted_key.public_key,
            )
            extraction_root = Path(
                tempfile.mkdtemp(
                    prefix=".extract-",
                    dir=self.paths.staging,
                )
            )
            extraction_root.rmdir()
            try:
                extract_archive_safely(
                    archive_path,
                    extraction_root,
                )
                validate_required_members(extraction_root)
                checksums = load_checksums(extraction_root)
                verified_hashes = verify_member_checksums(
                    extraction_root,
                    checksums,
                )
                defense_pack = load_and_validate_defense_pack(
                    root=extraction_root,
                    schema_path=(
                        self.schema_root
                        / "defense-pack-consumer.schema.json"
                    ),
                )
                validate_identity_consistency(
                    manifest=manifest,
                    defense_pack=defense_pack,
                )
                compatibility = load_json(
                    extraction_root / "compatibility.json"
                )
                descriptor = descriptor_from_defense_pack(
                    defense_pack
                )
                compatibility_result = evaluate_compatibility(
                    descriptor=descriptor,
                    compatibility=compatibility,
                    platform_identity=platform_identity,
                )
                if compatibility_result.status != "compatible":
                    raise PackCompatibilityFailure(
                        "; ".join(
                            compatibility_result.limitations
                        )
                    )
                self.retirement.require_not_retired(
                    pack_id=defense_pack["pack_id"],
                    pack_version=defense_pack["version"],
                )
                return self.store.install(
                    extracted_root=extraction_root,
                    manifest=manifest,
                    defense_pack=defense_pack,
                    manifest_path=manifest_path,
                    archive_sha256=archive_sha256,
                    signer_key_id=trusted_key.key_id,
                    content_hashes=verified_hashes,
                    limitations=list(
                        compatibility_result.limitations
                    ),
                )
            finally:
                shutil.rmtree(
                    extraction_root,
                    ignore_errors=True,
                )
        except PackError as error:
            self.quarantine.record(
                reason_code=type(error).__name__,
                reason=str(error),
                manifest_path=manifest_path,
                archive_path=archive_path,
            )
            raise
        except Exception as error:
            self.quarantine.record(
                reason_code="unexpected_installation_failure",
                reason=str(error),
                manifest_path=manifest_path,
                archive_path=archive_path,
            )
            raise
EOF
cat > src/l9_debt_lsp/packs/activation.py <<'EOF'
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from l9_debt_lsp.contracts.schema import SchemaValidator
from .errors import ActivationError, RollbackError
from .hashing import namespaced_hash
from .jsonio import (
    append_canonical_jsonl,
    load_json,
    write_canonical_json,
)
from .models import ActivationPointer, InstalledPack
from .paths import StatePaths
from .retirement import RetirementRegistry
from .store import PackStore
from .time import format_utc, utc_now
class ActivationManager:
    def __init__(
        self,
        *,
        paths: StatePaths,
        schema_root: Path,
    ) -> None:
        self.paths = paths
        self.store = PackStore(
            packs_root=paths.packs,
            staging_root=paths.staging,
        )
        self.retirement = RetirementRegistry(
            paths.retired_packs,
            schema_root / "retired-pack-registry.schema.json",
        )
        self.pointer_validator = SchemaValidator(
            schema_root / "activation-pointer.schema.json"
        )
    def load_active(self) -> ActivationPointer | None:
        return self._load_pointer(self.paths.active)
    def load_previous(self) -> ActivationPointer | None:
        return self._load_pointer(self.paths.previous)
    def activate(
        self,
        pack_id: str,
        *,
        operation: str = "activate",
    ) -> ActivationPointer:
        self.paths.initialize()
        target = self.store.verify_integrity(pack_id)
        self.retirement.require_not_retired(
            pack_id=target.pack_id,
            pack_version=target.pack_version,
        )
        current = self.load_active()
        occurred_at = format_utc(utc_now())
        activation_id = namespaced_hash(
            "activation_",
            {
                "operation": operation,
                "target_pack_id": target.pack_id,
                "previous_pack_id": (
                    current.pack_id
                    if current is not None
                    else None
                ),
                "target_archive_sha256": (
                    target.archive_sha256
                ),
                "occurred_at": occurred_at,
            },
        )
        pointer = self._pointer_from_pack(
            target,
            activated_at=occurred_at,
            activation_id=activation_id,
        )
        try:
            if current is not None and current.pack_id != target.pack_id:
                write_canonical_json(
                    self.paths.previous,
                    current.as_dict(),
                )
            write_canonical_json(
                self.paths.active,
                pointer.as_dict(),
            )
            self._append_history(
                operation=operation,
                activation_id=activation_id,
                target_pack_id=target.pack_id,
                previous_pack_id=(
                    current.pack_id
                    if current is not None
                    else None
                ),
                occurred_at=occurred_at,
                status="succeeded",
                limitations=[],
            )
            return pointer
        except Exception as error:
            self._append_history(
                operation=operation,
                activation_id=activation_id,
                target_pack_id=target.pack_id,
                previous_pack_id=(
                    current.pack_id
                    if current is not None
                    else None
                ),
                occurred_at=occurred_at,
                status="failed",
                limitations=[str(error)],
            )
            raise ActivationError(
                f"atomic pack activation failed: {error}"
            ) from error
    def rollback(self) -> ActivationPointer:
        previous = self.load_previous()
        if previous is None:
            raise RollbackError(
                "no previous-known-good pack is available"
            )
        try:
            return self.activate(
                previous.pack_id,
                operation="rollback",
            )
        except Exception as error:
            raise RollbackError(
                f"rollback failed: {error}"
            ) from error
    def recover(self) -> dict[str, Any]:
        self.paths.initialize()
        active = self.load_active()
        previous = self.load_previous()
        result: dict[str, Any] = {
            "schema_version": "l9.activation-recovery/v1",
            "status": "valid",
            "active_pack_id": None,
            "previous_pack_id": None,
            "limitations": [],
        }
        if active is not None:
            try:
                installed = self.store.verify_integrity(
                    active.pack_id
                )
                self.retirement.require_not_retired(
                    pack_id=installed.pack_id,
                    pack_version=installed.pack_version,
                )
                result["active_pack_id"] = active.pack_id
            except Exception as error:
                result["status"] = "degraded"
                result["limitations"].append(
                    f"active pack invalid: {error}"
                )
        if previous is not None:
            try:
                installed = self.store.verify_integrity(
                    previous.pack_id
                )
                self.retirement.require_not_retired(
                    pack_id=installed.pack_id,
                    pack_version=installed.pack_version,
                )
                result["previous_pack_id"] = previous.pack_id
            except Exception as error:
                result["status"] = "degraded"
                result["limitations"].append(
                    f"previous-known-good invalid: {error}"
                )
        return result
    def _load_pointer(
        self,
        path: Path,
    ) -> ActivationPointer | None:
        if not path.is_file():
            return None
        document = load_json(path)
        self.pointer_validator.validate(document)
        return ActivationPointer(
            pack_id=document["pack_id"],
            pack_version=document["pack_version"],
            archive_sha256=document["archive_sha256"],
            corpus_snapshot=document["corpus_snapshot"],
            compiler_version=document["compiler_version"],
            taxonomy_version=document["taxonomy_version"],
            sdk_contract_version=document[
                "sdk_contract_version"
            ],
            activated_at=document["activated_at"],
            activation_id=document["activation_id"],
        )
    @staticmethod
    def _pointer_from_pack(
        pack: InstalledPack,
        *,
        activated_at: str,
        activation_id: str,
    ) -> ActivationPointer:
        return ActivationPointer(
            pack_id=pack.pack_id,
            pack_version=pack.pack_version,
            archive_sha256=pack.archive_sha256,
            corpus_snapshot=pack.corpus_snapshot,
            compiler_version=pack.compiler_version,
            taxonomy_version=pack.taxonomy_version,
            sdk_contract_version=pack.sdk_contract_version,
            activated_at=activated_at,
            activation_id=activation_id,
        )
    def _append_history(
        self,
        *,
        operation: str,
        activation_id: str,
        target_pack_id: str,
        previous_pack_id: str | None,
        occurred_at: str,
        status: str,
        limitations: list[str],
    ) -> None:
        sequence = 1
        if self.paths.activation_history.is_file():
            with self.paths.activation_history.open(
                "r",
                encoding="utf-8",
            ) as stream:
                sequence += sum(
                    1 for line in stream if line.strip()
                )
        append_canonical_jsonl(
            self.paths.activation_history,
            {
                "schema_version": (
                    "l9.pack-activation-history-entry/v1"
                ),
                "sequence": sequence,
                "operation": operation,
                "activation_id": activation_id,
                "target_pack_id": target_pack_id,
                "previous_pack_id": previous_pack_id,
                "occurred_at": occurred_at,
                "status": status,
                "limitations": sorted(set(limitations)),
            },
        )
EOF
###############################################################################
# 5. Consumer defense-pack schema
###############################################################################
cat > schemas/lsp/defense-pack-consumer.schema.json <<'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "l9://lsp/defense-pack-consumer/v1",
  "title": "L9 LSP Defense Pack Consumer Schema",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "pack_id",
    "version",
    "corpus_snapshot",
    "analysis_run",
    "compilation_id",
    "compiler_version",
    "taxonomy_version",
    "SDK_contract_version",
    "compatibility",
    "rules",
    "checksums",
    "signature_metadata",
    "limitations"
  ],
  "properties": {
    "schema_version": {
      "const": "l9.debt-defense/v1"
    },
    "pack_id": {
      "type": "string",
      "pattern": "^pack_[0-9a-f]{64}$"
    },
    "version": {
      "type": "string",
      "minLength": 1
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
      "type": "string"
    },
    "taxonomy_version": {
      "type": "string"
    },
    "SDK_contract_version": {
      "const": "l9.integration-contract/v1"
    },
    "compatibility": {
      "type": "object"
    },
    "rules": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "canonical_rule_id",
          "candidate_id",
          "kind",
          "score",
          "source_path",
          "source_sha256",
          "lineage"
        ],
        "properties": {
          "canonical_rule_id": {
            "type": "string"
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
          "score": {
            "type": "number",
            "minimum": 4,
            "maximum": 5
          },
          "source_path": {
            "type": "string",
            "pattern": "^rules/"
          },
          "source_sha256": {
            "type": "string",
            "pattern": "^[0-9a-f]{64}$"
          },
          "lineage": {
            "type": "object"
          }
        }
      }
    },
    "checksums": {
      "type": "object"
    },
    "signature_metadata": {
      "type": "object",
      "required": [
        "required",
        "algorithm",
        "signed_value"
      ],
      "properties": {
        "required": {
          "const": true
        },
        "algorithm": {
          "const": "Ed25519"
        },
        "signed_value": {
          "const": "archive_sha256"
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
# 6. Runtime capabilities
###############################################################################
cat > src/l9_debt_lsp/runtime/capabilities.py <<'EOF'
from __future__ import annotations
from typing import Any
def phase_capabilities() -> dict[str, Any]:
    """Return the LSP-P1 capability surface."""
    return {
        "schema_version": "l9.lsp-server-capabilities/v1",
        "phase": "LSP-P1",
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
            "diagnostics": False,
            "code_actions": False,
            "telemetry": False,
        },
        "limitations": [
            "Pack discovery and download remain external.",
            "SDK incremental analysis is implemented in LSP-P2.",
            "Diagnostics are implemented after SDK session integration.",
            "Code actions and telemetry remain disabled.",
        ],
    }
EOF
###############################################################################
# 7. CLI
###############################################################################
cat > src/l9_debt_lsp/cli.py <<'EOF'
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Sequence
from .packs.activation import ActivationManager
from .packs.installer import PackInstaller
from .packs.paths import StatePaths, default_state_root
from .packs.store import PackStore
from .runtime.capabilities import phase_capabilities
def schema_root() -> Path:
    return Path("schemas/lsp").resolve()
def state_paths(value: Path | None) -> StatePaths:
    return StatePaths(
        (value or default_state_root()).expanduser().resolve()
    )
def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="l9-debt-lsp-contracts"
    )
    root.add_argument(
        "--state-root",
        type=Path,
        default=None,
    )
    commands = root.add_subparsers(
        dest="command",
        required=True,
    )
    commands.add_parser("capabilities")
    install = commands.add_parser("install-pack")
    install.add_argument(
        "--manifest",
        type=Path,
        required=True,
    )
    install.add_argument(
        "--archive",
        type=Path,
        required=True,
    )
    install.add_argument("--platform")
    activate = commands.add_parser("activate-pack")
    activate.add_argument("--pack-id", required=True)
    commands.add_parser("rollback-pack")
    commands.add_parser("active-pack")
    commands.add_parser("recover-state")
    verify = commands.add_parser("verify-installed-pack")
    verify.add_argument("--pack-id", required=True)
    return root
def emit(value: object) -> None:
    print(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
def main(argv: Sequence[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    paths = state_paths(arguments.state_root)
    schemas = schema_root()
    if arguments.command == "capabilities":
        emit(phase_capabilities())
        return 0
    if arguments.command == "install-pack":
        installed = PackInstaller(
            paths=paths,
            schema_root=schemas,
        ).install(
            manifest_path=arguments.manifest.resolve(),
            archive_path=arguments.archive.resolve(),
            platform_identity=arguments.platform,
        )
        emit(installed.as_dict())
        return 0
    manager = ActivationManager(
        paths=paths,
        schema_root=schemas,
    )
    if arguments.command == "activate-pack":
        pointer = manager.activate(arguments.pack_id)
        emit(pointer.as_dict())
        return 0
    if arguments.command == "rollback-pack":
        pointer = manager.rollback()
        emit(pointer.as_dict())
        return 0
    if arguments.command == "active-pack":
        active = manager.load_active()
        emit(
            active.as_dict()
            if active is not None
            else {
                "schema_version": (
                    "l9.pack-activation-pointer/v1"
                ),
                "status": "none",
            }
        )
        return 0
    if arguments.command == "recover-state":
        emit(manager.recover())
        return 0
    if arguments.command == "verify-installed-pack":
        store = PackStore(
            packs_root=paths.packs,
            staging_root=paths.staging,
        )
        installed = store.verify_integrity(
            arguments.pack_id
        )
        emit(installed.as_dict())
        return 0
    raise AssertionError("unreachable")
if __name__ == "__main__":
    raise SystemExit(main())
EOF
###############################################################################
# 8. Tests
###############################################################################
cat > tests/security/test_archive_security.py <<'EOF'
from __future__ import annotations
import io
import tarfile
from pathlib import Path
import pytest
from l9_debt_lsp.packs.archive import (
    extract_archive_safely,
    inspect_archive,
)
from l9_debt_lsp.packs.errors import ArchiveSecurityError
def create_archive(
    path: Path,
    members: dict[str, bytes],
) -> None:
    with tarfile.open(path, "w:gz") as archive:
        for name, content in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
def test_rejects_parent_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.tar.gz"
    create_archive(archive, {"../escape.txt": b"escape"})
    with pytest.raises(ArchiveSecurityError):
        inspect_archive(archive)
def test_rejects_absolute_path(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.tar.gz"
    create_archive(archive, {"/tmp/escape.txt": b"escape"})
    with pytest.raises(ArchiveSecurityError):
        inspect_archive(archive)
def test_rejects_case_folded_duplicate_paths(
    tmp_path: Path,
) -> None:
    archive = tmp_path / "unsafe.tar.gz"
    create_archive(
        archive,
        {
            "rules/Rule.yaml": b"one",
            "rules/rule.yaml": b"two",
        },
    )
    with pytest.raises(ArchiveSecurityError):
        inspect_archive(archive)
def test_safe_archive_is_extracted(tmp_path: Path) -> None:
    archive = tmp_path / "safe.tar.gz"
    destination = tmp_path / "out"
    create_archive(
        archive,
        {
            "defense-pack.json": b"{}",
            "compatibility.json": b"{}",
            "checksums.json": b"{}",
            "rules/example.yaml": b"id: example\n",
        },
    )
    result = extract_archive_safely(
        archive,
        destination,
    )
    assert result.member_count == 4
    assert (
        destination / "rules/example.yaml"
    ).read_bytes() == b"id: example\n"
EOF
cat > tests/security/test_trust_registry.py <<'EOF'
from __future__ import annotations
import base64
import json
from pathlib import Path
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)
from l9_debt_lsp.packs.errors import TrustError
from l9_debt_lsp.packs.trust import (
    TrustRegistry,
    public_key_id,
)
ROOT = Path(__file__).resolve().parents[2]
def public_key() -> str:
    private = Ed25519PrivateKey.generate()
    raw = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(raw).decode("ascii")
def write_registry(
    path: Path,
    key: str,
    *,
    enabled: bool,
) -> str:
    key_id = public_key_id(key)
    path.write_text(
        json.dumps(
            {
                "schema_version": (
                    "l9.trusted-key-registry/v1"
                ),
                "keys": [
                    {
                        "key_id": key_id,
                        "algorithm": "Ed25519",
                        "public_key": key,
                        "enabled": enabled,
                        "usages": [
                            "defense-pack-verification"
                        ],
                        "issuer": "test",
                        "not_before": None,
                        "not_after": None,
                        "limitations": []
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return key_id
def test_enabled_key_is_accepted(tmp_path: Path) -> None:
    registry_path = tmp_path / "keys.json"
    key = public_key()
    key_id = write_registry(
        registry_path,
        key,
        enabled=True,
    )
    registry = TrustRegistry(
        registry_path,
        ROOT
        / "schemas/lsp/trusted-key-registry.schema.json",
    )
    result = registry.require_verification_key(
        key_id=key_id,
        embedded_public_key=key,
    )
    assert result.key_id == key_id
def test_disabled_key_is_rejected(tmp_path: Path) -> None:
    registry_path = tmp_path / "keys.json"
    key = public_key()
    key_id = write_registry(
        registry_path,
        key,
        enabled=False,
    )
    registry = TrustRegistry(
        registry_path,
        ROOT
        / "schemas/lsp/trusted-key-registry.schema.json",
    )
    with pytest.raises(TrustError):
        registry.require_verification_key(
            key_id=key_id,
            embedded_public_key=key,
        )
EOF
cat > tests/security/test_signature.py <<'EOF'
from __future__ import annotations
import base64
import hashlib
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)
from l9_debt_lsp.packs.errors import SignatureError
from l9_debt_lsp.packs.signature import (
    verify_archive_digest,
)
def test_valid_signature_is_accepted() -> None:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    digest = hashlib.sha256(b"archive").hexdigest()
    signature = private.sign(bytes.fromhex(digest))
    verify_archive_digest(
        archive_sha256=digest,
        signature_base64=base64.b64encode(
            signature
        ).decode("ascii"),
        public_key_base64=base64.b64encode(
            public
        ).decode("ascii"),
    )
def test_modified_digest_is_rejected() -> None:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    digest = hashlib.sha256(b"archive").hexdigest()
    signature = private.sign(bytes.fromhex(digest))
    modified = hashlib.sha256(b"modified").hexdigest()
    with pytest.raises(SignatureError):
        verify_archive_digest(
            archive_sha256=modified,
            signature_base64=base64.b64encode(
                signature
            ).decode("ascii"),
            public_key_base64=base64.b64encode(
                public
            ).decode("ascii"),
        )
EOF
cat > tests/runtime/test_activation.py <<'EOF'
from __future__ import annotations
import json
from pathlib import Path
from l9_debt_lsp.packs.activation import ActivationManager
from l9_debt_lsp.packs.paths import StatePaths
from l9_debt_lsp.packs.store import PackStore
ROOT = Path(__file__).resolve().parents[2]
def create_installed_pack(
    paths: StatePaths,
    *,
    pack_id: str,
    version: str,
    archive_hash: str,
) -> None:
    root = paths.packs / pack_id
    root.mkdir(parents=True)
    defense_pack = {
        "pack_id": pack_id,
        "version": version,
        "corpus_snapshot": (
            "cs_" + "b" * 64
        ),
        "compiler_version": "1.0.0",
        "taxonomy_version": "1.0.0",
        "SDK_contract_version": (
            "l9.integration-contract/v1"
        )
    }
    installation = {
        "schema_version": (
            "l9.pack-installation-record/v1"
        ),
        "pack_id": pack_id,
        "pack_version": version,
        "archive_sha256": archive_hash,
        "manifest_sha256": "c" * 64,
        "signer_key_id": "key_" + "d" * 64,
        "compatibility_state": "compatible",
        "installed_at": "2026-07-18T00:00:00Z",
        "content_hashes": {},
        "limitations": []
    }
    for name, value in {
        "manifest.json": {},
        "defense-pack.json": defense_pack,
        "compatibility.json": {},
        "checksums.json": {},
        "installation.json": installation,
    }.items():
        (root / name).write_text(
            json.dumps(value),
            encoding="utf-8",
        )
    (root / "archive.sha256").write_text(
        archive_hash + "\n",
        encoding="ascii",
    )
def test_activation_retains_previous_known_good(
    tmp_path: Path,
) -> None:
    paths = StatePaths(tmp_path / "state")
    paths.initialize()
    first = "pack_" + "1" * 64
    second = "pack_" + "2" * 64
    create_installed_pack(
        paths,
        pack_id=first,
        version="1.0.0",
        archive_hash="a" * 64,
    )
    create_installed_pack(
        paths,
        pack_id=second,
        version="2.0.0",
        archive_hash="b" * 64,
    )
    manager = ActivationManager(
        paths=paths,
        schema_root=ROOT / "schemas/lsp",
    )
    manager.activate(first)
    manager.activate(second)
    assert manager.load_active().pack_id == second
    assert manager.load_previous().pack_id == first
def test_rollback_reactivates_previous_pack(
    tmp_path: Path,
) -> None:
    paths = StatePaths(tmp_path / "state")
    paths.initialize()
    first = "pack_" + "1" * 64
    second = "pack_" + "2" * 64
    create_installed_pack(
        paths,
        pack_id=first,
        version="1.0.0",
        archive_hash="a" * 64,
    )
    create_installed_pack(
        paths,
        pack_id=second,
        version="2.0.0",
        archive_hash="b" * 64,
    )
    manager = ActivationManager(
        paths=paths,
        schema_root=ROOT / "schemas/lsp",
    )
    manager.activate(first)
    manager.activate(second)
    result = manager.rollback()
    assert result.pack_id == first
    assert manager.load_active().pack_id == first
    assert manager.load_previous().pack_id == second
EOF
cat > tests/runtime/test_activation_failure_preserves_state.py <<'EOF'
from __future__ import annotations
import json
from pathlib import Path
import pytest
from l9_debt_lsp.packs.activation import ActivationManager
from l9_debt_lsp.packs.errors import PackValidationError
from l9_debt_lsp.packs.paths import StatePaths
ROOT = Path(__file__).resolve().parents[2]
def test_invalid_target_does_not_replace_active_pack(
    tmp_path: Path,
) -> None:
    paths = StatePaths(tmp_path / "state")
    paths.initialize()
    active_id = "pack_" + "a" * 64
    root = paths.packs / active_id
    root.mkdir(parents=True)
    installation = {
        "schema_version": (
            "l9.pack-installation-record/v1"
        ),
        "pack_id": active_id,
        "pack_version": "1.0.0",
        "archive_sha256": "b" * 64,
        "manifest_sha256": "c" * 64,
        "signer_key_id": "key_" + "d" * 64,
        "compatibility_state": "compatible",
        "installed_at": "2026-07-18T00:00:00Z",
        "content_hashes": {},
        "limitations": []
    }
    defense_pack = {
        "pack_id": active_id,
        "version": "1.0.0",
        "corpus_snapshot": "cs_" + "e" * 64,
        "compiler_version": "1.0.0",
        "taxonomy_version": "1.0.0",
        "SDK_contract_version": (
            "l9.integration-contract/v1"
        )
    }
    for name, document in {
        "manifest.json": {},
        "defense-pack.json": defense_pack,
        "compatibility.json": {},
        "checksums.json": {},
        "installation.json": installation,
    }.items():
        (root / name).write_text(
            json.dumps(document),
            encoding="utf-8",
        )
    (root / "archive.sha256").write_text(
        "b" * 64 + "\n",
        encoding="ascii",
    )
    manager = ActivationManager(
        paths=paths,
        schema_root=ROOT / "schemas/lsp",
    )
    manager.activate(active_id)
    with pytest.raises(PackValidationError):
        manager.activate("pack_" + "f" * 64)
    assert manager.load_active().pack_id == active_id
EOF
###############################################################################
# 9. ADRs and roadmap
###############################################################################
cat > docs/architecture/ADRs/ADR-LSP-006-trusted-pack-installation.md <<'EOF'
# ADR-LSP-006: Defense packs are untrusted until fully verified
- Status: Accepted
- Phase: LSP-P1
## Decision
Downloaded defense-pack artifacts are treated as hostile input.
Installation requires:
1. manifest schema validation;
2. trusted signer resolution;
3. archive SHA-256 validation;
4. Ed25519 signature verification;
5. bounded archive inspection;
6. safe extraction;
7. member checksum verification;
8. defense-pack schema validation;
9. compatibility validation;
10. retirement validation.
No failed artifact can modify active or previous-known-good state.
EOF
cat > docs/architecture/ADRs/ADR-LSP-007-installation-and-activation-separation.md <<'EOF'
# ADR-LSP-007: Installation and activation are separate operations
- Status: Accepted
- Phase: LSP-P1
## Decision
Successful installation places an immutable pack in content-addressed local
storage but does not activate it.
Activation requires an explicit pack identity and is performed atomically.
This prevents download, discovery, or installation processes from silently
changing editor behavior.
EOF
cat > docs/architecture/ADRs/ADR-LSP-008-previous-known-good.md <<'EOF'
# ADR-LSP-008: Retain previous-known-good pack state
- Status: Accepted
- Phase: LSP-P1
## Decision
Every successful activation preserves the former active pack as the
previous-known-good pack.
Rollback activates that exact immutable pack without recompilation or network
access.
EOF
python3 - <<'PY'
from pathlib import Path
path = Path("ROADMAP.md")
text = path.read_text(encoding="utf-8")
text = text.replace(
    """## LSP-P1 — Pack protocol
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
""",
    """## LSP-P1 — Pack protocol
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
""",
)
path.write_text(text, encoding="utf-8")
PY
###############################################################################
# 10. CI
###############################################################################
cat > .github/workflows/phase-2-pack-protocol.yml <<'EOF'
name: LSP-P1 Pack Protocol
on:
  pull_request:
  push:
    branches:
      - main
permissions:
  contents: read
jobs:
  pack-protocol:
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
      - name: Security tests
        run: pytest tests/security
      - name: Pack tests
        run: pytest tests/packs
      - name: Runtime tests
        run: pytest tests/runtime
      - name: Architecture tests
        run: pytest tests/architecture
      - name: Contract tests
        run: pytest tests/contracts
      - name: Full test suite
        run: pytest --cov=l9_debt_lsp --cov-report=term-missing
      - name: Ruff
        run: ruff check .
      - name: Mypy
        run: mypy src
      - name: Capabilities
        run: l9-debt-lsp-contracts capabilities
EOF
###############################################################################
# 11. README update
###############################################################################
cat >> README.md <<'EOF'
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
“.l9/pack-protocol-contract.yaml”,
“schemas/lsp/publication-manifest.schema.json”,
“schemas/lsp/trusted-key-registry.schema.json”,
“schemas/lsp/activation-pointer.schema.json”,
“src/l9_debt_lsp/packs/installer.py”,
“src/l9_debt_lsp/packs/activation.py”,
“src/l9_debt_lsp/packs/archive.py”,
“src/l9_debt_lsp/packs/signature.py”,
“src/l9_debt_lsp/packs/trust.py”,
“tests/security/test_archive_security.py”,
“tests/runtime/test_activation.py”,
]

missing = [
path for path in required
if not (root / path).is_file()
]

if missing:
raise SystemExit(
f”LSP-P1 required files missing: {missing}”
)

for schema_path in sorted(
(root / “schemas/lsp”).glob(”*.json”)
):
schema = json.loads(
schema_path.read_text(encoding=“utf-8”)
)
Draft202012Validator.check_schema(schema)

prohibited_runtime_terms = (
“corpus_compiler”,
“intelligenceoutputspath”,
“refreshcorpus”,
“mine_patterns”,
)

for source_path in (
root / “src/l9_debt_lsp”
).rglob(”*.py”):
content = source_path.read_text(
encoding=“utf-8”
).lower()

for term in prohibited_runtime_terms:
    if term in content:
        raise SystemExit(
            f"prohibited runtime term {term!r} "
            f"found in {source_path}"
        )

print(
json.dumps(
{
“schema_version”: “l9.phase-build-result/v1”,
“repository”: “Quantum-L9/l9-ci-debt-lsp”,
“phase”: “LSP-P1”,
“status”: “built”,
“pack_verification”: “fail-closed”,
“installation”: “immutable”,
“activation”: “explicit-atomic”,
“rollback”: “previous-known-good”,
“corpus_dependency”: “prohibited”
},
sort_keys=True,
separators=(”,”, “:”),
)
)
PY

printf ‘\n’
printf ‘LSP-P1 build complete.\n’
printf ‘\n’
printf ‘Implemented:\n’
printf ’  - trusted Ed25519 signer registry\n’
printf ’  - publication-manifest validation\n’
printf ’  - archive SHA-256 validation\n’
printf ’  - detached signature verification\n’
printf ’  - bounded safe archive extraction\n’
printf ’  - member checksum verification\n’
printf ’  - immutable content-addressed installation\n’
printf ’  - quarantine metadata\n’
printf ’  - compatibility and retirement rejection\n’
printf ’  - explicit atomic activation\n’
printf ’  - previous-known-good retention\n’
printf ’  - offline rollback\n’
printf ’  - startup state recovery\n’
printf ‘\n’
printf ‘Next phase: LSP-P2 — SDK AnalysisSession integration, document overlays, cancellation, bounded invalidation, and stale-result suppression.\n’

:::
This phase keeps normal editor serving independent of network access and ensures no unverified, incompatible, corrupted, or retired pack can replace known-good runtime state.