from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .delivery_state import DeliveryStateStore
from .events import EventFactory
from .health import telemetry_health
from .identity import (
    InstallationIdentityStore,
    random_identity,
)
from .models import (
    TelemetryContext,
    TelemetryEvent,
)
from .paths import TelemetryPaths
from .policy import TelemetryPolicyStore
from .spool import TelemetrySpool
from .transport import TelemetryTransport


class TelemetryService:
    def __init__(
        self,
        *,
        paths: TelemetryPaths,
        schema_root: Path,
        client_name: str,
        client_version: str,
        lsp_version: str,
    ) -> None:
        self.paths = paths
        self.paths.initialize()
        self.policy_store = TelemetryPolicyStore(
            path=paths.policy,
            schema_path=(schema_root / "telemetry-policy.schema.json"),
        )
        self.identity_store = InstallationIdentityStore(paths.installation_id)
        self.context = TelemetryContext(
            installation_id=(self.identity_store.load_or_create()),
            session_id=random_identity("session_"),
            client_name=client_name,
            client_version=client_version,
            lsp_version=lsp_version,
        )
        self.factory = EventFactory(self.context)
        self.delivery_state = DeliveryStateStore(paths.delivery_state)

    def emit(
        self,
        *,
        event_type: str,
        **values: Any,
    ) -> TelemetryEvent | None:
        policy = self.policy_store.load()
        if not policy.persistence_enabled:
            return None
        event = self.factory.create(
            event_type=event_type,
            **values,
        )
        spool = TelemetrySpool(
            event_root=self.paths.events,
            dead_letter_root=self.paths.dead_letter,
            retention_days=policy.retention_days,
        )
        spool.append(event)
        return event

    async def deliver_once(self) -> dict[str, Any]:
        policy = self.policy_store.load()
        spool = TelemetrySpool(
            event_root=self.paths.events,
            dead_letter_root=self.paths.dead_letter,
            retention_days=policy.retention_days,
        )
        transport = TelemetryTransport(
            policy=policy,
            spool=spool,
            state_store=self.delivery_state,
            authorization_token=os.environ.get("L9_TELEMETRY_AUTH_TOKEN"),
        )
        return await transport.deliver_once()

    def health(self) -> dict[str, Any]:
        policy = self.policy_store.load()
        spool = TelemetrySpool(
            event_root=self.paths.events,
            dead_letter_root=self.paths.dead_letter,
            retention_days=policy.retention_days,
        )
        return telemetry_health(
            policy=policy,
            spool=spool,
            delivery_state=self.delivery_state,
        )

    def delete_all(self) -> None:
        policy = self.policy_store.load()
        spool = TelemetrySpool(
            event_root=self.paths.events,
            dead_letter_root=self.paths.dead_letter,
            retention_days=policy.retention_days,
        )
        spool.clear()
        self.identity_store.rotate()
