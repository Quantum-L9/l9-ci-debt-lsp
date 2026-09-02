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
            "developer_identity_telemetry": False,
        },
        # Which upstream inputs are real, and which are architecture intent.
        # `sdk_finding_validation` above is genuine code -- the consumer schema
        # exists and is enforced -- but validating a contract is not the same as
        # receiving one, and the capability list alone cannot express that.
        "input_status": {
            "active": [
                {
                    "contract": "l9.debt-defense/v1",
                    "producer": "Quantum-L9/l9-ci-debt-intelligence",
                    "note": "Defense-pack consumption is the editor path in v0.1.",
                }
            ],
            "inactive": [
                {
                    "contract": "l9.sdk-finding/v1",
                    "producer": None,
                    "status": "planned",
                    "note": (
                        "Direct SDK finding consumption is inactive. No producer "
                        "emits l9.sdk-finding/v1; the SDK's tokens are "
                        "l9.finding-bundle/v1, l9.observation, l9.gate-result/v1, "
                        "and l9.agent-review-projection/v1. The shapes also "
                        "differ beyond renaming, and the severity vocabularies "
                        "share only 'critical' and 'unknown', so activating this "
                        "requires an explicit projection contract rather than a "
                        "field mapping."
                    ),
                }
            ],
        },
        "limitations": [
            "A concrete public SDK AnalysisSession binding must be configured.",
            (
                "Direct SDK finding consumption (l9.sdk-finding/v1) is inactive "
                "in v0.1: no producer emits the contract. The active editor "
                "input is intelligence defense packs (l9.debt-defense/v1)."
            ),
            (
                "Telemetry delivery requires explicit policy and an allowlisted "
                "HTTPS endpoint."
            ),
            (
                "Effectiveness aggregation and rule governance remain owned by "
                "Debt Intelligence."
            ),
        ],
    }
