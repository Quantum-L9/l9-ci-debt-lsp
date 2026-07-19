from __future__ import annotations

from pathlib import Path

from l9_debt_lsp.contracts.schema import SchemaValidator
from l9_debt_lsp.packs.jsonio import (
    load_json,
    write_canonical_json,
)

from .errors import TelemetryPolicyError
from .models import TelemetryPolicy

DEFAULT_POLICY: dict[str, object] = {
    "schema_version": "l9.telemetry-policy/v1",
    "mode": "disabled",
    "consent": "not_granted",
    "endpoint": None,
    "endpoint_allowlist": [],
    "retention_days": 30,
    "organization_policy_id": None,
    "limitations": [],
}


class TelemetryPolicyStore:
    def __init__(
        self,
        *,
        path: Path,
        schema_path: Path,
    ) -> None:
        self.path = path
        self.schema_path = schema_path

    def initialize(self) -> None:
        if not self.path.is_file():
            write_canonical_json(
                self.path,
                DEFAULT_POLICY,
            )

    def load(self) -> TelemetryPolicy:
        self.initialize()
        document = load_json(self.path)
        SchemaValidator(self.schema_path).validate(document)
        policy = TelemetryPolicy(
            mode=document["mode"],
            consent=document["consent"],
            endpoint=document["endpoint"],
            endpoint_allowlist=tuple(sorted(set(document["endpoint_allowlist"]))),
            retention_days=document["retention_days"],
            organization_policy_id=document["organization_policy_id"],
            limitations=tuple(sorted(set(document["limitations"]))),
        )
        self._validate_semantics(policy)
        return policy

    def save(self, policy: TelemetryPolicy) -> None:
        self._validate_semantics(policy)
        write_canonical_json(
            self.path,
            {
                "schema_version": "l9.telemetry-policy/v1",
                "mode": policy.mode,
                "consent": policy.consent,
                "endpoint": policy.endpoint,
                "endpoint_allowlist": list(policy.endpoint_allowlist),
                "retention_days": policy.retention_days,
                "organization_policy_id": (policy.organization_policy_id),
                "limitations": list(policy.limitations),
            },
        )

    @staticmethod
    def _validate_semantics(policy: TelemetryPolicy) -> None:
        if policy.mode == "disabled":
            if policy.delivery_enabled:
                raise TelemetryPolicyError("disabled telemetry cannot deliver events")
        if policy.mode == "local_only" and policy.endpoint is not None:
            raise TelemetryPolicyError("local-only telemetry cannot define an endpoint")
        if policy.delivery_enabled and policy.endpoint is None:
            raise TelemetryPolicyError(
                "delivery-enabled telemetry requires an endpoint"
            )
        if policy.endpoint is not None:
            if not policy.endpoint.startswith("https://"):
                raise TelemetryPolicyError("telemetry endpoint must use HTTPS")
            if not any(
                policy.endpoint.startswith(prefix)
                for prefix in policy.endpoint_allowlist
            ):
                raise TelemetryPolicyError("telemetry endpoint is not allowlisted")
