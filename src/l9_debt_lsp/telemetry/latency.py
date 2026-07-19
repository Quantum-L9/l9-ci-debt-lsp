from __future__ import annotations


def latency_bucket(
    latency_ms: float,
    *,
    cancelled: bool = False,
    timed_out: bool = False,
) -> str:
    if timed_out:
        return "timed_out"
    if cancelled:
        return "cancelled"
    if latency_ms < 25:
        return "lt_25ms"
    if latency_ms < 50:
        return "25_49ms"
    if latency_ms < 100:
        return "50_99ms"
    if latency_ms < 200:
        return "100_199ms"
    if latency_ms < 500:
        return "200_499ms"
    if latency_ms < 1000:
        return "500_999ms"
    if latency_ms < 2000:
        return "1_2s"
    if latency_ms < 5000:
        return "2_5s"
    return "gt_5s"
