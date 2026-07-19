from __future__ import annotations

DOCUMENT_P95_MS = 200.0
EVALUATION_TIMEOUT_MS = 5000.0


def classify_latency(
    latency_ms: float,
    *,
    cancelled: bool = False,
    timed_out: bool = False,
) -> str:
    if timed_out:
        return "timed_out"
    if cancelled:
        return "cancelled"
    if latency_ms <= DOCUMENT_P95_MS:
        return "within_budget"
    if latency_ms <= DOCUMENT_P95_MS * 2:
        return "elevated"
    return "exceeded"
