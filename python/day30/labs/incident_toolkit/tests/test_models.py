"""Tests for Pydantic models."""
from __future__ import annotations

from incident_toolkit.models import AssessResult, CheckResult, HealthSummary, IncidentContext


def test_incident_context_generates_id():
    ctx = IncidentContext(environment="staging")
    assert len(ctx.incident_id) == 8


def test_assess_result_unhealthy_property():
    results = [
        CheckResult(name="ok", url="http://x", ok=True, latency_ms=1.0),
        CheckResult(name="bad", url="http://y", ok=False, latency_ms=2.0),
    ]
    assess = AssessResult(
        incident_id="abc",
        environment="staging",
        summary=HealthSummary(total=2, healthy=1, unhealthy=1),
        results=results,
    )
    assert len(assess.unhealthy) == 1
    assert assess.unhealthy[0].name == "bad"
