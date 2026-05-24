"""FastAPI app with Prometheus metrics and structured logging."""
from __future__ import annotations

import os
import random
import time

import structlog
from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from logging_setup import configure_logging

configure_logging(json_output=os.environ.get("LOG_FORMAT", "json") == "json")
log = structlog.get_logger()

WORK_TOTAL = Counter("ops_work_total", "Work units processed", ["status"])
WORK_DURATION = Histogram("ops_work_duration_seconds", "Work duration")
IN_FLIGHT = Gauge("ops_in_flight", "Work in progress")

app = FastAPI(title="Metrics Exporter Lab")


@app.middleware("http")
async def request_metrics(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    log.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2),
    )
    return response


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/work")
async def do_work() -> dict:
    IN_FLIGHT.inc()
    start = time.perf_counter()
    try:
        time.sleep(random.uniform(0.05, 0.3))
        if random.random() < 0.1:
            WORK_TOTAL.labels(status="failed").inc()
            log.error("work_failed", reason="simulated failure")
            return {"status": "failed"}
        WORK_TOTAL.labels(status="success").inc()
        log.info("work_succeeded")
        return {"status": "ok"}
    finally:
        WORK_DURATION.observe(time.perf_counter() - start)
        IN_FLIGHT.dec()


if __name__ == "__main__":
    from prometheus_client import start_http_server

    start_http_server(9100)
    log.info("metrics_server_started", port=9100)
    while True:
        time.sleep(3600)
