"""Deploy action routes."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from deps import verify_token
from models import DeployRequest, DeployStatus

router = APIRouter(prefix="/deploys", tags=["deploys"])

_store: dict[str, DeployStatus] = {}


def _simulate_deploy(deploy_id: str) -> None:
    if deploy_id in _store:
        _store[deploy_id] = _store[deploy_id].model_copy(update={"status": "succeeded"})


@router.post("", response_model=DeployStatus, status_code=202)
async def create_deploy(
    body: DeployRequest,
    background_tasks: BackgroundTasks,
    _token: Annotated[str, Depends(verify_token)],
) -> DeployStatus:
    deploy_id = str(uuid.uuid4())[:8]
    status = DeployStatus(
        id=deploy_id,
        name=body.name,
        env=body.env,
        status="running",
        replicas=body.replicas,
        image=body.image,
    )
    _store[deploy_id] = status
    background_tasks.add_task(_simulate_deploy, deploy_id)
    return status


@router.get("/{deploy_id}", response_model=DeployStatus)
async def get_deploy(deploy_id: str) -> DeployStatus:
    if deploy_id not in _store:
        raise HTTPException(status_code=404, detail="Deploy not found")
    return _store[deploy_id]
