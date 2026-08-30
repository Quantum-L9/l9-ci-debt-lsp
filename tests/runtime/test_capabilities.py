from __future__ import annotations

from l9_debt_lsp.runtime.capabilities import phase_capabilities


def test_final_capabilities_are_complete_and_fail_closed() -> None:
    capabilities = phase_capabilities()
    assert capabilities["phase"] == "LSP-P5"
    assert capabilities["repository_status"] == "architecturally_complete"

    enabled = (
        "pack_installation",
        "pack_activation",
        "rollback",
        "document_overlays",
        "diagnostic_projection",
        "bounded_code_actions",
        "telemetry_policy",
        "privacy_validation",
        "telemetry_health",
    )
    for capability in enabled:
        assert capabilities["capabilities"][capability] is True

    prohibited = (
        "arbitrary_command_execution",
        "autonomous_multi_file_repair",
        "source_content_telemetry",
        "absolute_path_telemetry",
        "developer_identity_telemetry",
    )
    for capability in prohibited:
        assert capabilities["capabilities"][capability] is False


def test_defense_pack_is_the_only_active_upstream_input() -> None:
    """The intelligence -> LSP defense-pack seam is the real one.

    It is the one cross-repository contract pair in the constellation whose
    producer and consumer schemas actually agree, so it is what v0.1 ships.
    """
    active = phase_capabilities()["input_status"]["active"]
    assert [entry["contract"] for entry in active] == ["l9.debt-defense/v1"]
    assert active[0]["producer"] == "Quantum-L9/l9-ci-debt-intelligence"


def test_direct_sdk_finding_consumption_is_declared_inactive() -> None:
    """Validating a contract is not the same as receiving one.

    `sdk_finding_validation` is real code -- the consumer schema exists and is
    enforced -- but nothing emits `l9.sdk-finding/v1`. Beyond the missing
    producer the shapes cannot be reconciled by renaming, and the severity
    vocabularies share only `critical` and `unknown`, so this needs an explicit
    projection contract rather than a field mapping.
    """
    inactive = phase_capabilities()["input_status"]["inactive"]
    entry = next(item for item in inactive if item["contract"] == "l9.sdk-finding/v1")
    assert entry["status"] == "planned"
    assert entry["producer"] is None
    assert entry["note"]


def test_no_contract_is_both_active_and_inactive() -> None:
    status = phase_capabilities()["input_status"]
    active = {entry["contract"] for entry in status["active"]}
    inactive = {entry["contract"] for entry in status["inactive"]}
    assert not (active & inactive)
