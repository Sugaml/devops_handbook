"""Tests for health module."""
from __future__ import annotations

from incident_toolkit.health import summarize
from incident_toolkit.models import CheckResult


def test_summarize():
    results = [
        CheckResult(name="a", url="http://a", ok=True, latency_ms=1.0),
        CheckResult(name="b", url="http://b", ok=False, latency_ms=2.0, error="timeout"),
    ]
    summary = summarize(results)
    assert summary.total == 2
    assert summary.healthy == 1
    assert summary.unhealthy == 1
