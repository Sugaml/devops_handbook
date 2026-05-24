"""Pydantic models for incident workflows."""
from __future__ import annotations

from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class CheckResult(BaseModel):
    name: str
    url: str
    ok: bool
    status_code: int | None = None
    latency_ms: float
    error: str | None = None


class HealthSummary(BaseModel):
    total: int
    healthy: int
    unhealthy: int


class IncidentContext(BaseModel):
    incident_id: str = Field(default_factory=lambda: uuid4().hex[:8])
    severity: Literal["sev1", "sev2", "sev3"] = "sev2"
    environment: Literal["dev", "staging", "prod"] = "staging"
    dry_run: bool = True


class AssessResult(BaseModel):
    incident_id: str
    environment: str
    summary: HealthSummary
    results: list[CheckResult]

    @property
    def unhealthy(self) -> list[CheckResult]:
        return [r for r in self.results if not r.ok]


class HostRecord(BaseModel):
    name: str
    group: str
    ansible_host: str
    env: str


class InventoryGroup(BaseModel):
    name: str
    hosts: list[HostRecord]


class PlaybookResult(BaseModel):
    playbook: str
    rc: int
    dry_run: bool
    stdout: str = ""


class RemediateResult(BaseModel):
    incident_id: str
    playbook: str
    dry_run: bool
    success: bool
    rc: int
