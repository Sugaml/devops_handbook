# Day 26 — Structured Logging & Prometheus Metrics

**Goal:** Instrument Python ops tools with JSON structured logs and Prometheus metrics so on-call engineers can correlate failures, measure SLOs, and scrape `/metrics` from Kubernetes or systemd services.

**Time:** 4–5 hours

**Prerequisites:** Day 25 (FastAPI); basic Prometheus/Grafana concepts

---

## 1. Why structured logging?

Plain `print()` in production:

```
Deploy failed for web
```

Structured JSON log:

```json
{"timestamp": "2026-05-24T10:15:00Z", "level": "error", "event": "deploy_failed",
 "service": "web", "env": "prod", "deploy_id": "a1b2", "error": "timeout"}
```

Log aggregators (Loki, Elasticsearch, CloudWatch) can filter on fields — not regex on free text.

| Unstructured | Structured |
|--------------|------------|
| Hard to alert on | Field-based alerts |
| Lost context | Request ID, user, region attached |
| Inconsistent | Schema per service |

---

## 2. structlog setup

See `labs/logging_setup.py`:

```python
import structlog
import logging
import sys

def configure_logging(json_output: bool = True, level: str = "INFO") -> None:
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    structlog.configure(processors=processors)
```

Bind context per request or job:

```python
log = structlog.get_logger()
structlog.contextvars.bind_contextvars(deploy_id="abc", env="staging")
log.info("deploy_started", service="web", replicas=3)
```

---

## 3. Logging standards for ops tools

Include consistently:

- `timestamp`, `level`, `event` (snake_case verb_noun)
- `service` / `component` name
- `request_id` or `trace_id` when handling HTTP
- `duration_ms` on completion events
- Never log secrets, tokens, or full env dicts

```python
log.info("ansible_playbook_finished", playbook="site.yml", rc=0, duration_ms=12400)
log.error("health_check_failed", target="https://api/v1/health", status_code=503)
```

---

## 4. Prometheus client basics

```bash
pip install prometheus-client
```

Metric types:

| Type | Use case | Example |
|------|----------|---------|
| Counter | Monotonically increasing | `deploy_total`, `errors_total` |
| Gauge | Current value up/down | `in_flight_requests`, queue depth |
| Histogram | Latency distribution | `http_request_duration_seconds` |
| Summary | Quantiles (client-side) | Less common with histograms + recording rules |

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

DEPLOY_TOTAL = Counter("ops_deploy_total", "Deploy attempts", ["env", "status"])
REQUEST_LATENCY = Histogram("ops_request_seconds", "HTTP latency", ["method", "path"])
IN_FLIGHT = Gauge("ops_in_flight", "Active operations")

IN_FLIGHT.inc()
try:
    ...
    DEPLOY_TOTAL.labels(env="prod", status="success").inc()
finally:
    IN_FLIGHT.dec()
```

Expose metrics:

```python
start_http_server(9100)  # standalone script
# or mount in FastAPI (see metrics_exporter.py)
```

---

## 5. FastAPI + Prometheus middleware

Track request count and latency without blocking:

```python
from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
HTTP_LATENCY = Histogram("http_request_duration_seconds", "HTTP latency", ["method", "path"])

@app.middleware("http")
async def prometheus_middleware(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    path = request.url.path
    HTTP_REQUESTS.labels(request.method, path, response.status_code).inc()
    HTTP_LATENCY.labels(request.method, path).observe(duration)
    return response
```

Normalize path labels — avoid high cardinality (`/users/12345` → `/users/{id}`).

---

## 6. Kubernetes scraping

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ops-api
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
```

Or use PodMonitor / ServiceMonitor with Prometheus Operator.

---

## 7. Correlating logs and metrics

Use the same `request_id` in logs and as a metric label only when cardinality is bounded. Prefer:

1. Log: full detail with request_id
2. Metrics: aggregate counters/histograms without request_id
3. Trace: OpenTelemetry span links both (future enhancement)

---

## 8. Lab — Day 26

Work from `python/day26/labs/`.

1. Install: `pip install structlog prometheus-client fastapi uvicorn`.
2. Run `python logged_worker.py --count 5` — observe JSON logs on stdout.
3. Run `python metrics_exporter.py` and curl `http://127.0.0.1:9100/metrics`.
4. Start `uvicorn metrics_exporter:app --port 8080`; hit `/work` several times; scrape `/metrics`.
5. Confirm counters increment: `ops_work_total`, `ops_work_duration_seconds`.
6. Toggle `LOG_FORMAT=console` for human-readable dev output.
7. **Stretch:** Add a Grafana dashboard JSON snippet recording `rate(ops_work_total[5m])`.

**Success criteria:** Logs are valid JSON; Prometheus text format exposes custom metrics.

---

## 9. DevOps connections

- **SLO dashboards:** Error rate = `rate(errors_total[5m]) / rate(requests_total[5m])`.
- **Alertmanager:** Page on-call when `ops_deploy_total{status="failed"}` increases.
- **Incident response:** Filter Loki by `deploy_id` from a failing metric spike.

---

## Quick reference

| Task | Command |
|------|---------|
| JSON logs | `LOG_FORMAT=json python logged_worker.py` |
| Metrics server | `python metrics_exporter.py` |
| Scrape | `curl localhost:9100/metrics` |
| FastAPI metrics | `curl localhost:8080/metrics` |
| Bind context | `structlog.contextvars.bind_contextvars(request_id=...)` |

**Next:** [Day 27 — asyncio & concurrent health checks](../day27/)
