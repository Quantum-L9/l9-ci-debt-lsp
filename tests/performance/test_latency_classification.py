from __future__ import annotations

from l9_debt_lsp.analysis.latency import classify_latency


def test_latency_budget_classes() -> None:
    assert classify_latency(50) == "within_budget"
    assert classify_latency(250) == "elevated"
    assert classify_latency(500) == "exceeded"
    assert classify_latency(10, cancelled=True) == "cancelled"
    assert classify_latency(5001, timed_out=True) == "timed_out"
