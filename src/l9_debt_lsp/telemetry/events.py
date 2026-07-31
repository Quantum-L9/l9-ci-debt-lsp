from __future__ import annotations

from l9_debt_lsp.packs.time import format_utc, utc_now

from .identity import event_identity
from .models import (
    TelemetryContext,
    TelemetryEvent,
)
from .privacy import validate_privacy

SUPPORTED_EVENT_TYPES = {
    "diagnostic_shown",
    "diagnostic_dismissed",
    "false_positive_disposition",
    "quick_fix_offered",
    "quick_fix_applied",
    "quick_fix_rejected",
    "quick_fix_outcome",
    "rule_outcome",
    "latency_bucket",
    "pack_activated",
    "pack_rollback",
}
DISPOSITIONS = {
    "false_positive",
    "not_actionable",
    "accepted_risk",
    "duplicate",
    "obsolete",
    "valid_finding",
    "unknown",
}
OUTCOMES = {
    "finding_present",
    "finding_resolved",
    "finding_persisted",
    "finding_dismissed",
    "finding_dispositioned",
    "resolved",
    "new_findings_introduced",
    "edit_reverted",
    "outcome_unknown",
}


class EventFactory:
    def __init__(self, context: TelemetryContext) -> None:
        self.context = context
        self._sequence = 0

    def create(
        self,
        *,
        event_type: str,
        rule_pack_id: str | None = None,
        rule_pack_version: str | None = None,
        corpus_snapshot: str | None = None,
        canonical_rule_id: str | None = None,
        provider_rule_id: str | None = None,
        finding_id: str | None = None,
        analysis_request_id: str | None = None,
        action_id: str | None = None,
        template_id: str | None = None,
        outcome: str | None = None,
        disposition: str | None = None,
        latency_bucket: str | None = None,
        limitations: tuple[str, ...] = (),
    ) -> TelemetryEvent:
        if event_type not in SUPPORTED_EVENT_TYPES:
            raise ValueError(f"unsupported telemetry event type: {event_type}")
        if disposition is not None and disposition not in DISPOSITIONS:
            raise ValueError(f"unsupported telemetry disposition: {disposition}")
        if outcome is not None and outcome not in OUTCOMES:
            raise ValueError(f"unsupported telemetry outcome: {outcome}")
        self._sequence += 1
        occurred_at = format_utc(utc_now())
        identity_input = {
            "event_type": event_type,
            "occurred_at": occurred_at,
            "installation_id": self.context.installation_id,
            "session_id": self.context.session_id,
            "sequence": self._sequence,
            "rule_pack_id": rule_pack_id,
            "canonical_rule_id": canonical_rule_id,
            "finding_id": finding_id,
            "action_id": action_id,
            "outcome": outcome,
            "disposition": disposition,
            "latency_bucket": latency_bucket,
        }
        event = TelemetryEvent(
            event_id=event_identity(identity_input),
            event_type=event_type,
            occurred_at=occurred_at,
            installation_id=self.context.installation_id,
            session_id=self.context.session_id,
            sequence=self._sequence,
            client_name=self.context.client_name,
            client_version=self.context.client_version,
            lsp_version=self.context.lsp_version,
            rule_pack_id=rule_pack_id,
            rule_pack_version=rule_pack_version,
            corpus_snapshot=corpus_snapshot,
            canonical_rule_id=canonical_rule_id,
            provider_rule_id=provider_rule_id,
            finding_id=finding_id,
            analysis_request_id=analysis_request_id,
            action_id=action_id,
            template_id=template_id,
            outcome=outcome,
            disposition=disposition,
            latency_bucket=latency_bucket,
            limitations=tuple(sorted(set(limitations))),
        )
        validate_privacy(event.as_dict())
        return event
