"""Host registry routes."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from models import HostSummary

router = APIRouter(prefix="/hosts", tags=["hosts"])

HOSTS_FILE = Path(__file__).resolve().parent.parent / "hosts.json"


def load_hosts() -> list[dict]:
    return json.loads(HOSTS_FILE.read_text())


@router.get("", response_model=list[HostSummary])
async def list_hosts() -> list[HostSummary]:
    return [HostSummary(**host, reachable=True) for host in load_hosts()]


@router.get("/{name}", response_model=HostSummary)
async def get_host(name: str) -> HostSummary:
    for host in load_hosts():
        if host["name"] == name:
            return HostSummary(**host, reachable=True)
    raise HTTPException(status_code=404, detail=f"Host {name} not found")
