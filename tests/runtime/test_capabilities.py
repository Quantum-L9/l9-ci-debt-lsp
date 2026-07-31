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
