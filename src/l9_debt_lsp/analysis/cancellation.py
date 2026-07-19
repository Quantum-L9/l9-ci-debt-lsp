from __future__ import annotations

import asyncio
from dataclasses import dataclass

from .errors import AnalysisCancelledError


@dataclass(frozen=True)
class CancellationState:
    cancelled: bool
    reason: str | None


class CancellationToken:
    def __init__(self) -> None:
        self._event = asyncio.Event()
        self._reason: str | None = None

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    @property
    def reason(self) -> str | None:
        return self._reason

    def cancel(self, reason: str) -> None:
        if self._event.is_set():
            return
        self._reason = reason
        self._event.set()

    async def wait(self) -> None:
        await self._event.wait()

    def raise_if_cancelled(self) -> None:
        if self.cancelled:
            raise AnalysisCancelledError(self._reason or "cancelled")

    def snapshot(self) -> CancellationState:
        return CancellationState(
            cancelled=self.cancelled,
            reason=self.reason,
        )
