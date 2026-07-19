from __future__ import annotations

from pathlib import Path
from typing import Any

from l9_debt_lsp.packs.paths import StatePaths
from l9_debt_lsp.telemetry.latency import latency_bucket
from l9_debt_lsp.telemetry.paths import TelemetryPaths
from l9_debt_lsp.telemetry.service import TelemetryService


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
            rule_pack_version=data.get("rule_pack_version"),
            corpus_snapshot=data.get("corpus_snapshot"),
            canonical_rule_id=data.get("canonical_rule_id"),
            provider_rule_id=data.get("provider_rule_id"),
            finding_id=data.get("finding_id"),
            analysis_request_id=data.get("analysis_request_id"),
            limitations=tuple(data.get("limitations", [])),
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
            rule_pack_version=data.get("rule_pack_version"),
            corpus_snapshot=data.get("corpus_snapshot"),
            canonical_rule_id=data.get("canonical_rule_id"),
            provider_rule_id=data.get("provider_rule_id"),
            finding_id=data.get("finding_id"),
            analysis_request_id=data.get("analysis_request_id"),
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
            rule_pack_version=data.get("rule_pack_version"),
            corpus_snapshot=data.get("corpus_snapshot"),
            canonical_rule_id=data.get("canonical_rule_id"),
            provider_rule_id=data.get("provider_rule_id"),
            finding_id=data.get("finding_id"),
            analysis_request_id=data.get("analysis_request_id"),
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
            cancelled=(analysis.get("status") == "cancelled"),
            timed_out=(analysis.get("latency_class") == "timed_out"),
        )
        self.service.emit(
            event_type="latency_bucket",
            rule_pack_id=analysis.get("active_pack_id"),
            analysis_request_id=analysis.get("request_id"),
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
            rule_pack_id=provenance.get("rule_pack_id"),
            rule_pack_version=provenance.get("rule_pack_version"),
            corpus_snapshot=provenance.get("corpus_snapshot"),
            canonical_rule_id=provenance.get("canonical_rule_id"),
            provider_rule_id=provenance.get("provider_rule_id"),
            finding_id=provenance.get("finding_id"),
            analysis_request_id=provenance.get("analysis_request_id"),
            action_id=provenance.get("action_id"),
            template_id=provenance.get("template_id"),
            outcome=outcome,
            limitations=tuple(provenance.get("limitations", [])),
        )
