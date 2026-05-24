"""Health probe routes."""
from __future__ import annotations

from fastapi import APIRouter

from models import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])

_checks = {"config_loaded": True, "host_registry": True}


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/health/ready", response_model=ReadyResponse)
async def ready() -> ReadyResponse:
    return ReadyResponse(ready=all(_checks.values()), checks=dict(_checks))
