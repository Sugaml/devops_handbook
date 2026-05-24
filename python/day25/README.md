# Day 25 — FastAPI for Internal Ops Tools & Dashboards

**Goal:** Build a lightweight internal API for deploy status, health aggregation, and operator actions — with auth hooks, OpenAPI docs, and production-ready patterns.

**Time:** 5–6 hours

**Prerequisites:** Day 23 (Pydantic models); Day 24 (CLI patterns)

---

## 1. When to use FastAPI for ops

| Use FastAPI | Use something else |
|-------------|-------------------|
| Internal dashboards backing React/Vue | Public customer API at massive scale |
| Webhook receivers (GitHub, PagerDuty) | Heavy batch ETL |
| Self-service restart/scale endpoints | Simple static status page |
| Aggregating metrics from multiple systems | Full Grafana replacement |

FastAPI gives you **async I/O**, **automatic OpenAPI**, and **Pydantic validation** — ideal for platform team tools.

---

## 2. Project layout

```
python/day25/labs/
├── ops_api.py           # FastAPI app
├── models.py            # request/response schemas
├── deps.py              # dependency injection
└── routers/
    ├── health.py
    ├── hosts.py
    └── deploys.py
```

Install and run:

```bash
pip install "fastapi[standard]" uvicorn httpx
cd python/day25/labs
uvicorn ops_api:app --reload --port 8080
```

Open http://127.0.0.1:8080/docs for interactive Swagger UI.

---

## 3. Application factory pattern

```python
from fastapi import FastAPI
from routers import health, hosts, deploys

def create_app() -> FastAPI:
    app = FastAPI(
        title="Handbook Ops API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.include_router(health.router)
    app.include_router(hosts.router, prefix="/api/v1")
    app.include_router(deploys.router, prefix="/api/v1")
    return app

app = create_app()
```

Keeps tests able to import a fresh app instance without side effects.

---

## 4. Typed endpoints with Pydantic

```python
from pydantic import BaseModel, Field

class HostSummary(BaseModel):
    name: str
    group: str
    env: str
    reachable: bool = False

@router.get("/hosts", response_model=list[HostSummary])
async def list_hosts():
    return [HostSummary(**h) for h in load_hosts()]
```

`response_model` strips extra fields and validates output — prevents accidental secret leakage.

---

## 5. Dependency injection for auth and config

Never hardcode tokens. Use FastAPI `Depends`:

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

async def verify_token(
    creds: HTTPAuthorizationCredentials | None = Security(security),
) -> str:
    if creds is None or creds.credentials != settings.api_token:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return creds.credentials
```

Protect mutating routes:

```python
@router.post("/deploys", dependencies=[Depends(verify_token)])
async def trigger_deploy(body: DeployRequest):
    ...
```

For production, integrate OAuth2 proxy, mTLS, or SSO at the ingress layer.

---

## 6. Background tasks for long operations

Don't block the event loop on Ansible runs or cloud API polls:

```python
from fastapi import BackgroundTasks

@router.post("/deploys/{deploy_id}/retry")
async def retry_deploy(deploy_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_deploy_async, deploy_id)
    return {"status": "accepted", "deploy_id": deploy_id}
```

Return `202 Accepted` for async work; expose job status via `/deploys/{id}`.

---

## 7. Middleware: request ID and timing

```python
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Duration-Ms"] = f"{duration_ms:.1f}"
        return response
```

Correlate API logs with upstream load balancer request IDs.

---

## 8. Testing with httpx

```python
from fastapi.testclient import TestClient
from ops_api import create_app

client = TestClient(create_app())

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_deploy_requires_auth():
    r = client.post("/api/v1/deploys", json={"name": "web", "env": "staging"})
    assert r.status_code == 401
```

Use `TestClient` for sync tests; `httpx.AsyncClient` for async endpoint tests.

---

## 9. Running behind reverse proxy

Production deployment sketch:

```bash
uvicorn ops_api:app --host 0.0.0.0 --port 8080 --workers 2 --proxy-headers
```

Kubernetes Deployment with liveness `/health` and readiness `/health/ready` (see `ops_api.py`).

---

## 10. Lab — Day 25

Work from `python/day25/labs/`.

1. Start API: `uvicorn ops_api:app --reload --port 8080`.
2. Open `/docs`; call `GET /api/v1/hosts`.
3. Call `GET /health` and `GET /health/ready`.
4. POST to `/api/v1/deploys` without token — expect 401.
5. Set `OPS_API_TOKEN=handbook-lab` and retry with `Authorization: Bearer handbook-lab`.
6. Trigger deploy with invalid body — observe 422 validation errors.
7. **Stretch:** Add a `GET /api/v1/deploys/{id}` status endpoint backed by in-memory store.

**Success criteria:** OpenAPI docs load; auth protects POST; health probes return correct JSON.

---

## 11. DevOps connections

- **Backstage / internal portals:** FastAPI serves catalog and action plugins.
- **ChatOps:** Slack slash commands POST to your FastAPI webhooks.
- **GitOps visibility:** Expose Argo CD / Flux application status through a unified API layer.

---

## Quick reference

| Task | Command / URL |
|------|----------------|
| Run dev server | `uvicorn ops_api:app --reload` |
| OpenAPI UI | `http://127.0.0.1:8080/docs` |
| Health | `curl localhost:8080/health` |
| Auth header | `Authorization: Bearer $OPS_API_TOKEN` |
| Test | `pytest tests/test_api.py` |

**Next:** [Day 26 — Structured logging & Prometheus metrics](../day26/)
