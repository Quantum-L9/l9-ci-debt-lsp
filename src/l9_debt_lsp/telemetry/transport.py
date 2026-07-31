from __future__ import annotations

import gzip
import random
from typing import Any

import httpx

from l9_debt_lsp.contracts.canonical import canonical_json
from l9_debt_lsp.packs.time import format_utc, utc_now

from .delivery_state import DeliveryStateStore
from .errors import TelemetryTransportError
from .models import TelemetryPolicy
from .spool import TelemetrySpool

RETRYABLE_STATUSES = {
    408,
    425,
    429,
    500,
    502,
    503,
    504,
}


class TelemetryTransport:
    def __init__(
        self,
        *,
        policy: TelemetryPolicy,
        spool: TelemetrySpool,
        state_store: DeliveryStateStore,
        authorization_token: str | None = None,
    ) -> None:
        self.policy = policy
        self.spool = spool
        self.state_store = state_store
        self.authorization_token = authorization_token

    async def deliver_once(self) -> dict[str, Any]:
        state = self.state_store.load()
        if not self.policy.delivery_enabled:
            state["last_delivery_status"] = "delivery_disabled"
            self.state_store.save(state)
            return state
        if self.policy.endpoint is None:
            raise TelemetryTransportError("delivery endpoint is not configured")
        batch = self.spool.batch()
        if not batch:
            state["last_delivery_status"] = "queue_empty"
            self.state_store.save(state)
            return state
        paths = [path for path, _ in batch]
        body = b"\n".join(canonical_json(document) for _, document in batch) + b"\n"
        compressed = gzip.compress(body)
        headers = {
            "Content-Type": "application/x-ndjson",
            "Content-Encoding": "gzip",
            "User-Agent": "l9-ci-debt-lsp-telemetry/1",
        }
        if self.authorization_token:
            headers["Authorization"] = f"Bearer {self.authorization_token}"
        now = format_utc(utc_now())
        state["last_attempt_at"] = now
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    timeout=15.0,
                    connect=3.0,
                    read=10.0,
                ),
                follow_redirects=False,
                verify=True,
            ) as client:
                response = await client.post(
                    self.policy.endpoint,
                    headers=headers,
                    content=compressed,
                )
            if 200 <= response.status_code < 300:
                self.spool.acknowledge(paths)
                state["last_successful_delivery_at"] = now
                state["last_delivery_status"] = f"succeeded:{response.status_code}"
                state["consecutive_failures"] = 0
                state["next_attempt_at"] = None
                state["limitations"] = []
                self.state_store.save(state)
                return state
            if response.status_code in RETRYABLE_STATUSES:
                return self._record_retryable_failure(
                    state,
                    f"http_{response.status_code}",
                )
            for path in paths:
                self.spool.move_to_dead_letter(
                    path,
                    reason=f"http_{response.status_code}",
                )
            state["last_delivery_status"] = f"dead_lettered:{response.status_code}"
            state["consecutive_failures"] = 0
            state["next_attempt_at"] = None
            state["limitations"] = ["Telemetry batch was rejected permanently."]
            self.state_store.save(state)
            return state
        except (
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.TransportError,
        ) as error:
            return self._record_retryable_failure(
                state,
                type(error).__name__,
            )

    def _record_retryable_failure(
        self,
        state: dict[str, Any],
        reason: str,
    ) -> dict[str, Any]:
        failures = min(
            int(state.get("consecutive_failures", 0)) + 1,
            8,
        )
        base = min(300, 2 ** (failures - 1))
        delay = random.uniform(0, float(base))
        next_attempt = utc_now().timestamp() + delay
        import datetime as dt

        state["last_delivery_status"] = f"retryable_failure:{reason}"
        state["consecutive_failures"] = failures
        state["next_attempt_at"] = format_utc(
            dt.datetime.fromtimestamp(
                next_attempt,
                tz=dt.UTC,
            )
        )
        state["limitations"] = [
            "Telemetry delivery is degraded; editor behavior is unaffected."
        ]
        self.state_store.save(state)
        return state
