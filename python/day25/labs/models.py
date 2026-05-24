"""Pydantic schemas for ops API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HostSummary(BaseModel):
    name: str
    group: str
    env: str
    ansible_host: str
    reachable: bool = False


class DeployRequest(BaseModel):
    name: str = Field(min_length=1, max_length=63)
    env: Literal["dev", "staging", "prod"]
    replicas: int = Field(ge=1, le=50)
    image: str


class DeployStatus(BaseModel):
    id: str
    name: str
    env: str
    status: Literal["pending", "running", "succeeded", "failed"]
    replicas: int
    image: str


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    ready: bool
    checks: dict[str, bool]
