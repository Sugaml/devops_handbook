"""Prometheus metrics for incident workflows."""
from __future__ import annotations

from prometheus_client import Counter, Histogram

ASSESS_TOTAL = Counter(
    "incident_assess_total",
    "Incident assessments completed",
    ["status"],
)
REMEDIATE_TOTAL = Counter(
    "incident_remediate_total",
    "Remediation playbook runs",
    ["status", "dry_run"],
)
CHECK_DURATION = Histogram(
    "incident_check_duration_seconds",
    "Health check batch duration",
)
