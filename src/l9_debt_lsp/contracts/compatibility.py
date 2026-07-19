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
            isinstance(platforms, list) and platform_identity in platforms
        ),
        "runtime_rule_kinds_supported": set(descriptor.runtime_rule_kinds).issubset(
            ACCEPTED_RULE_KINDS
        ),
    }
    if isinstance(sdk, dict):
        checks["sdk_matrix_contract_matches"] = (
            sdk.get("contract") == descriptor.sdk_contract_version
        )
    else:
        checks["sdk_matrix_contract_matches"] = False
    if isinstance(lsp, dict):
        checks["lsp_consumer_contract_supported"] = (
            lsp.get("minimum_contract") == "l9.lsp-defense-consumer/v1"
        )
    else:
        checks["lsp_consumer_contract_supported"] = False
    failed = sorted(name for name, passed in checks.items() if not passed)
    return CompatibilityResult(
        status="compatible" if not failed else "incompatible",
        pack_id=descriptor.pack_id,
        pack_version=descriptor.pack_version,
        checks=checks,
        limitations=tuple(f"compatibility check failed: {name}" for name in failed),
    )
