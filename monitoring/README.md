# Monitoring & Observability for DevOps — 7-Day Handbook

A hands-on path from metrics fundamentals to production observability: **Prometheus**, **Grafana**, **Alertmanager**, log pipelines, exporters, and on-call runbooks. Each day builds on the last with a Docker lab stack you can run locally.

## Structure

| Day | Topic | Folder |
|-----|--------|--------|
| 1 | Observability pillars, Prometheus scrape model, first targets | [day1](./day1/) |
| 2 | PromQL — rates, aggregations, and debugging queries | [day2](./day2/) |
| 3 | Grafana — datasources, dashboards, variables | [day3](./day3/) |
| 4 | Alerting — recording rules, Alertmanager, routing | [day4](./day4/) |
| 5 | Logs — Loki, Promtail, correlating logs and metrics | [day5](./day5/) |
| 6 | Exporters, blackbox probes, service discovery | [day6](./day6/) |
| 7 | SLOs, incident response, capstone observability stack | [day7](./day7/) |

## Prerequisites

- Linux CLI and Docker ([Linux](../linux/README.md) Day 1–2, [Docker](../docker/README.md) Day 1–3).
- Basic HTTP and ports ([Network](../network/README.md) Day 3 helps).
- Optional: [Kubernetes](../kubernetes/README.md) Day 1+ for Day 6–7 kube-prometheus context.

## Lab environment

From this directory:

```bash
docker compose up -d
# Prometheus  → http://localhost:9090
# Grafana     → http://localhost:3000  (admin / handbook)
# Alertmanager→ http://localhost:9093
# Loki        → http://localhost:3100  (Day 5+)
```

Stop and reset:

```bash
docker compose down -v
```

## How to use this handbook

1. Start the lab stack before each session (`docker compose up -d`).
2. Run every PromQL query and explore Grafana panels yourself.
3. Complete each day's **Lab** before advancing.
4. On Day 7, assemble a personal **observability triage checklist** for on-call.

## Design notes

- Targets **Prometheus 2.x**, **Grafana 10+**, **Alertmanager 0.27+**, **Loki 2.x** (2025–2026 stable lines).
- Labs use isolated job names (`handbook_*`) so you do not collide with other local stacks.
- Production callouts cover cardinality, alert fatigue, and secret handling in notification channels.

## Progress checklist

```
[ ] Day 1  [ ] Day 4
[ ] Day 2  [ ] Day 5
[ ] Day 3  [ ] Day 6
[ ] Day 7 — capstone
```

## Related handbooks

| Handbook | Connection |
|----------|------------|
| [Docker](../docker/README.md) | cAdvisor, container metrics |
| [Kubernetes](../kubernetes/README.md) | kube-prometheus, ServiceMonitors |
| [AWS](../aws/README.md) | CloudWatch, AMP, managed Grafana |
| [Python](../python/README.md) | Day 26–27 — custom metrics and health checks |
| [SQL](../sql/README.md) | Day 15 — database monitoring queries |
