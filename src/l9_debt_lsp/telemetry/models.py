from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TelemetryPolicy:
    mode: str
    consent: str
    endpoint: str | None
    endpoint_allowlist: tuple[str, ...]
    retention_days: int
    organization_policy_id: str | None
    limitations: tuple[str, ...]

    @property
    def persistence_enabled(self) -> bool:
        return self.mode != "disabled"

    @property
    def delivery_enabled(self) -> bool:
        if self.mode == "user_opt_in":
            return self.consent == "granted"
        if self.mode == "organization_controlled":
            return self.consent == "organization_required"
        return False


@dataclass(frozen=True)
class TelemetryContext:
    installation_id: str
    session_id: str
    client_name: str
    client_version: str
    lsp_version: str


@dataclass(frozen=True)
class TelemetryEvent:
    event_id: str
    event_type: str
    occurred_at: str
    installation_id: str
    session_id: str
    sequence: int
    client_name: str
    client_version: str
    lsp_version: str
    rule_pack_id: str | None
    rule_pack_version: str | None
    corpus_snapshot: str | None
    canonical_rule_id: str | None
    provider_rule_id: str | None
    finding_id: str | None
    analysis_request_id: str | None
    action_id: str | None
    template_id: str | None
    outcome: str | None
    disposition: str | None
    latency_bucket: str | None
    limitations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "l9.telemetry-event/v1",
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "installation_id": self.installation_id,
            "session_id": self.session_id,
            "sequence": self.sequence,
            "client_name": self.client_name,
            "client_version": self.client_version,
            "lsp_version": self.lsp_version,
            "rule_pack_id": self.rule_pack_id,
            "rule_pack_version": self.rule_pack_version,
            "corpus_snapshot": self.corpus_snapshot,
            "canonical_rule_id": self.canonical_rule_id,
            "provider_rule_id": self.provider_rule_id,
            "finding_id": self.finding_id,
            "analysis_request_id": self.analysis_request_id,
            "action_id": self.action_id,
            "template_id": self.template_id,
            "outcome": self.outcome,
            "disposition": self.disposition,
            "latency_bucket": self.latency_bucket,
            "limitations": list(self.limitations),
        }
