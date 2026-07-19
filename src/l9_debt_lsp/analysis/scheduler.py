from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass

from l9_debt_lsp.packs.time import format_utc, utc_now

from .cancellation import CancellationToken
from .errors import (
    AnalysisCancelledError,
    AnalysisTimeoutError,
    DocumentNotFoundError,
    StaleAnalysisResultError,
)
from .identity import request_identity
from .latency import EVALUATION_TIMEOUT_MS, classify_latency
from .models import (
    AnalysisRequest,
    AnalysisResult,
    SDKAnalysisResult,
)
from .sdk_protocol import AnalysisSession
from .workspace import WorkspaceManager


@dataclass
class RunningAnalysis:
    request: AnalysisRequest
    cancellation: CancellationToken
    task: asyncio.Task[AnalysisResult]


class AnalysisScheduler:
    def __init__(
        self,
        *,
        sdk: AnalysisSession,
        workspaces: WorkspaceManager,
        maximum_global_evaluations: int = 4,
        maximum_workspace_evaluations: int = 2,
        timeout_ms: float = EVALUATION_TIMEOUT_MS,
    ) -> None:
        self._sdk = sdk
        self._workspaces = workspaces
        self._global_semaphore = asyncio.Semaphore(maximum_global_evaluations)
        self._workspace_semaphores: dict[
            str,
            asyncio.Semaphore,
        ] = defaultdict(lambda: asyncio.Semaphore(maximum_workspace_evaluations))
        self._document_locks: dict[
            tuple[str, str],
            asyncio.Lock,
        ] = defaultdict(asyncio.Lock)
        self._running: dict[
            tuple[str, str],
            RunningAnalysis,
        ] = {}
        self._timeout_seconds = timeout_ms / 1000.0
        self._state_lock = asyncio.Lock()

    async def evaluate(
        self,
        *,
        workspace_id: str,
        document_id: str,
    ) -> AnalysisResult:
        state = self._workspaces.get_workspace_nowait(workspace_id)
        overlay = state.documents.get(document_id)
        if overlay is None or overlay.state != "open":
            raise DocumentNotFoundError(document_id)
        if state.active_pack is None:
            raise RuntimeError("workspace has no active pack")
        request = AnalysisRequest(
            request_id=request_identity(
                workspace_id=workspace_id,
                workspace_generation=state.generation,
                document_id=document_id,
                document_version=overlay.version,
                active_pack_id=state.active_pack.pack_id,
            ),
            workspace_id=workspace_id,
            workspace_generation=state.generation,
            document_id=document_id,
            document_uri=overlay.uri,
            document_version=overlay.version,
            language_id=overlay.language_id,
            active_pack_id=state.active_pack.pack_id,
            active_pack_version=(state.active_pack.pack_version),
            created_at=format_utc(utc_now()),
            limitations=(),
        )
        cancellation = CancellationToken()
        key = (workspace_id, document_id)
        async with self._state_lock:
            previous = self._running.get(key)
            if previous is not None:
                previous.cancellation.cancel("document_updated")
            task = asyncio.create_task(
                self._execute(
                    request=request,
                    cancellation=cancellation,
                )
            )
            self._running[key] = RunningAnalysis(
                request=request,
                cancellation=cancellation,
                task=task,
            )
        try:
            return await task
        finally:
            async with self._state_lock:
                current = self._running.get(key)
                if (
                    current is not None
                    and current.request.request_id == request.request_id
                ):
                    self._running.pop(key, None)

    async def cancel_document(
        self,
        *,
        workspace_id: str,
        document_id: str,
        reason: str,
    ) -> None:
        key = (workspace_id, document_id)
        async with self._state_lock:
            running = self._running.get(key)
            if running is not None:
                running.cancellation.cancel(reason)

    async def cancel_workspace(
        self,
        *,
        workspace_id: str,
        reason: str,
    ) -> None:
        async with self._state_lock:
            for key, running in self._running.items():
                if key[0] == workspace_id:
                    running.cancellation.cancel(reason)

    async def shutdown(self) -> None:
        async with self._state_lock:
            running = tuple(self._running.values())
            for item in running:
                item.cancellation.cancel("server_shutdown")
        if running:
            await asyncio.gather(
                *(item.task for item in running),
                return_exceptions=True,
            )

    async def _execute(
        self,
        *,
        request: AnalysisRequest,
        cancellation: CancellationToken,
    ) -> AnalysisResult:
        started = time.monotonic()
        workspace_semaphore = self._workspace_semaphores[request.workspace_id]
        document_lock = self._document_locks[
            (request.workspace_id, request.document_id)
        ]
        try:
            async with self._global_semaphore:
                async with workspace_semaphore:
                    async with document_lock:
                        cancellation.raise_if_cancelled()
                        workspace = self._workspaces.get_workspace_nowait(
                            request.workspace_id
                        )
                        pack = workspace.active_pack
                        if pack is None:
                            raise RuntimeError("workspace has no active pack")
                        sdk_result = await asyncio.wait_for(
                            self._sdk.evaluate_document(
                                workspace_id=request.workspace_id,
                                document_id=request.document_id,
                                version=request.document_version,
                                pack=pack,
                                cancellation=cancellation,
                            ),
                            timeout=self._timeout_seconds,
                        )
                        cancellation.raise_if_cancelled()
                        self._validate_freshness(request)
                        await self._workspaces.update_dependencies(
                            workspace_id=request.workspace_id,
                            document_id=request.document_id,
                            dependencies=sdk_result.dependencies,
                        )
                        latency_ms = (time.monotonic() - started) * 1000.0
                        return self._result_from_sdk(
                            request=request,
                            sdk_result=sdk_result,
                            latency_ms=latency_ms,
                        )
        except TimeoutError as error:
            cancellation.cancel("timeout")
            latency_ms = (time.monotonic() - started) * 1000.0
            raise AnalysisTimeoutError(
                f"analysis exceeded {self._timeout_seconds:.3f}s"
            ) from error
        except AnalysisCancelledError:
            latency_ms = (time.monotonic() - started) * 1000.0
            return AnalysisResult(
                request_id=request.request_id,
                workspace_id=request.workspace_id,
                workspace_generation=(request.workspace_generation),
                document_id=request.document_id,
                document_version=request.document_version,
                active_pack_id=request.active_pack_id,
                status="cancelled",
                findings=(),
                limitations=(cancellation.reason or "cancelled",),
                latency_ms=latency_ms,
                latency_class=classify_latency(
                    latency_ms,
                    cancelled=True,
                ),
                completed_at=format_utc(utc_now()),
            )
        except StaleAnalysisResultError as error:
            latency_ms = (time.monotonic() - started) * 1000.0
            return AnalysisResult(
                request_id=request.request_id,
                workspace_id=request.workspace_id,
                workspace_generation=(request.workspace_generation),
                document_id=request.document_id,
                document_version=request.document_version,
                active_pack_id=request.active_pack_id,
                status="stale",
                findings=(),
                limitations=(str(error),),
                latency_ms=latency_ms,
                latency_class=classify_latency(latency_ms),
                completed_at=format_utc(utc_now()),
            )
        except Exception as error:
            latency_ms = (time.monotonic() - started) * 1000.0
            return AnalysisResult(
                request_id=request.request_id,
                workspace_id=request.workspace_id,
                workspace_generation=(request.workspace_generation),
                document_id=request.document_id,
                document_version=request.document_version,
                active_pack_id=request.active_pack_id,
                status="failed",
                findings=(),
                limitations=(f"analysis failed: {type(error).__name__}",),
                latency_ms=latency_ms,
                latency_class=classify_latency(latency_ms),
                completed_at=format_utc(utc_now()),
            )

    def _validate_freshness(
        self,
        request: AnalysisRequest,
    ) -> None:
        state = self._workspaces.get_workspace_nowait(request.workspace_id)
        if state.state != "open":
            raise StaleAnalysisResultError("workspace is no longer open")
        overlay = state.documents.get(request.document_id)
        if overlay is None or overlay.state != "open":
            raise StaleAnalysisResultError("document is no longer open")
        if overlay.version != request.document_version:
            raise StaleAnalysisResultError("document version advanced")
        if state.generation != request.workspace_generation:
            raise StaleAnalysisResultError("workspace generation changed")
        if (
            state.active_pack is None
            or state.active_pack.pack_id != request.active_pack_id
        ):
            raise StaleAnalysisResultError("active pack changed")

    @staticmethod
    def _result_from_sdk(
        *,
        request: AnalysisRequest,
        sdk_result: SDKAnalysisResult,
        latency_ms: float,
    ) -> AnalysisResult:
        limitations = tuple(sorted(set(sdk_result.limitations)))
        status = "complete" if sdk_result.complete else "incomplete"
        if status == "incomplete" and not limitations:
            limitations = ("SDK reported incomplete analysis without details.",)
        findings = tuple(
            sorted(
                sdk_result.findings,
                key=lambda finding: (
                    str(finding.get("canonical_rule_id", "")),
                    str(finding.get("finding_id", "")),
                ),
            )
        )
        return AnalysisResult(
            request_id=request.request_id,
            workspace_id=request.workspace_id,
            workspace_generation=(request.workspace_generation),
            document_id=request.document_id,
            document_version=request.document_version,
            active_pack_id=request.active_pack_id,
            status=status,
            findings=findings,
            limitations=limitations,
            latency_ms=latency_ms,
            latency_class=classify_latency(latency_ms),
            completed_at=format_utc(utc_now()),
        )
