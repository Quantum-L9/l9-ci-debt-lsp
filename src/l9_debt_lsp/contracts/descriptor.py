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
        sdk_contract_version=str(defense_pack["SDK_contract_version"]),
        runtime_rule_kinds=tuple(sorted(runtime_rule_kinds)),
        limitations=tuple(sorted(set(str(item) for item in limitations))),
    )
