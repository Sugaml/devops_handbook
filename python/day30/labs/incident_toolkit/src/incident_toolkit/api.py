"""Optional FastAPI sidecar for dashboards and ChatOps."""
from __future__ import annotations

from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from incident_toolkit.config import settings
from incident_toolkit.health import assess
from incident_toolkit.inventory import build_inventory_groups, load_hosts
from incident_toolkit.models import AssessResult, IncidentContext

security = HTTPBearer(auto_error=False)


async def verify_token(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> None:
    if creds is None or creds.credentials != settings.api_token:
        raise HTTPException(status_code=401, detail="Unauthorized")


def create_app() -> FastAPI:
    app = FastAPI(title="Incident Toolkit API", version="1.0.0")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metrics")
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/api/v1/inventory")
    async def inventory() -> list[dict]:
        return [g.model_dump() for g in build_inventory_groups(load_hosts())]

    @app.post("/api/v1/incidents/assess", response_model=AssessResult, dependencies=[Depends(verify_token)])
    async def post_assess(
        targets_path: str,
        background_tasks: BackgroundTasks,
        env: str = "staging",
    ) -> AssessResult:
        path = Path(targets_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="targets file not found")
        ctx = IncidentContext(environment=env)  # type: ignore[arg-type]
        result = await assess(path, ctx)
        background_tasks.add_task(lambda: None)
        return result

    return app
