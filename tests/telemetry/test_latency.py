from __future__ import annotations

from l9_debt_lsp.telemetry.latency import (
    latency_bucket,
)


def test_latency_is_bucketed_without_raw_delivery() -> None:
    assert latency_bucket(10) == "lt_25ms"
    assert latency_bucket(50) == "50_99ms"
    assert latency_bucket(250) == "200_499ms"
    assert latency_bucket(1500) == "1_2s"
    assert latency_bucket(6000) == "gt_5s"
    assert latency_bucket(1, cancelled=True) == "cancelled"
    assert latency_bucket(1, timed_out=True) == "timed_out"
