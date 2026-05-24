"""FastAPI ops dashboard API."""
from __future__ import annotations

import time
import uuid

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from routers import deploys, health, hosts


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Duration-Ms"] = f"{duration_ms:.1f}"
        return response


def create_app() -> FastAPI:
    app = FastAPI(
        title="Handbook Ops API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(RequestIDMiddleware)
    app.include_router(health.router)
    app.include_router(hosts.router, prefix="/api/v1")
    app.include_router(deploys.router, prefix="/api/v1")
    return app


app = create_app()
