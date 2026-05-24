# Day 1 — Observability Pillars & Prometheus Fundamentals

**Goal:** Understand metrics vs logs vs traces, how Prometheus pull-scraping works, and verify a multi-target lab stack.

**Time:** 4–5 hours

---

## 1. The three pillars

| Pillar | Question it answers | Typical tools |
|--------|---------------------|---------------|
| **Metrics** | How much / how fast / how many? | Prometheus, CloudWatch, Datadog |
| **Logs** | What happened on this request? | Loki, ELK, CloudWatch Logs |
| **Traces** | Where did latency go across services? | Jaeger, Tempo, X-Ray |

**DevOps use:** Metrics drive dashboards and alerts; logs explain failures; traces find cross-service bottlenecks.

---

## 2. Prometheus architecture (pull model)

```
  Targets (exporters, apps)  ◄── scrape ──  Prometheus  ──►  Grafana
        │                         │              │
        │                         └── rule eval ─┴──► Alertmanager
        └── expose /metrics HTTP endpoint
```

- **Scrape** — Prometheus polls `http://target/metrics` on an interval.
- **Time series** — identified by metric name + labels (`http_requests_total{method="GET"}`).
- **TSDB** — local storage (or remote write to long-term store in production).

Why pull? Central discovery, no agent push credentials on every app, easy to detect `up == 0`.

---

## 3. Start the lab stack

```bash
cd monitoring
docker compose up -d
docker compose ps
```

| URL | Purpose |
|-----|---------|
| http://localhost:9090 | Prometheus UI |
| http://localhost:3000 | Grafana (`admin` / `handbook`) |
| http://localhost:9093 | Alertmanager |
| http://localhost:8080 | Demo nginx app |

---

## 4. Explore Prometheus UI

### Targets health

Open **Status → Targets**. Expect `prometheus`, `node`, and `blackbox_http` jobs **UP**.

### Run instant queries

```promql
up
node_cpu_seconds_total
rate(node_cpu_seconds_total[5m])
```

### Understand `up`

`up{job="node"}` is `1` when last scrape succeeded, `0` when failed — your first SLO-adjacent signal.

---

## 5. Metric types (preview)

| Type | Example | PromQL note |
|------|---------|-------------|
| Counter | `http_requests_total` | Use `rate()` or `increase()` |
| Gauge | `memory_used_bytes` | Use directly |
| Histogram | `http_request_duration_seconds_bucket` | `histogram_quantile()` |
| Summary | client-side quantiles | Less common in modern stacks |

Day 2 goes deeper on PromQL.

---

## Lab

1. `docker compose up -d` and confirm all targets UP.
2. Query `up` and record which jobs exist.
3. Run `rate(node_cpu_seconds_total{mode="idle"}[5m])` — interpret one series.
4. Open Grafana → **Dashboards → Handbook → Node Overview** — confirm panels render.
5. Stop `node-exporter`: `docker stop handbook-node-exporter` — watch `up{job="node"}` flip to 0 within one scrape interval; restart container.

---

## Day 1 checklist

- [ ] Can explain pull vs push monitoring
- [ ] Found targets and ran basic PromQL
- [ ] Opened Grafana provisioned dashboard
- [ ] Simulated target failure with `up`

**Next:** [Day 2 — PromQL](../day2/)
