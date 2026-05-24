# Day 5 — Logs with Loki & Promtail

**Goal:** Ship container logs to Loki, query with LogQL, and correlate logs with Prometheus metrics in Grafana.

**Time:** 4–5 hours

---

## 1. Why Loki?

| ELK stack | Loki |
|-----------|------|
| Index full text | Index **labels** only |
| Heavy JVM heap | Cheaper at scale |
| Powerful but ops-heavy | Fits Grafana ecosystem |

Loki is **not** a replacement for full-text legal discovery — it is optimized for label-filtered operational logs.

---

## 2. Log pipeline in the lab

```
Docker containers → Promtail (docker_sd) → Loki → Grafana datasource
```

Configs: `labs/loki/loki-config.yml`, `labs/promtail/promtail-config.yml`.

Verify:

```bash
docker compose ps loki promtail
curl -s http://localhost:3100/ready
```

---

## 3. LogQL basics

```logql
{container="handbook-demo-app"}
{container=~".*prometheus.*"}
{container="handbook-prometheus"} |= "error"
{container="handbook-prometheus"} | json | level="error"
```

| Stage | Purpose |
|-------|---------|
| Label selector `{...}` | Required first — like Prometheus labels |
| `|=` / `!=` | Line filter |
| `| json` | Parse JSON log lines |
| `| rate()` | Metric queries from logs (advanced) |

---

## 4. Correlate logs + metrics

In Grafana:

1. Open a Prometheus dashboard panel (CPU).
2. **Panel menu → More → Copy link** or use **Split** view.
3. Add Loki panel with `{container="handbook-demo-app"}`.
4. Align time range around an incident.

Shared labels (`container`, `namespace`, `pod`) are the glue — design apps and infra to emit consistent labels.

---

## 5. Structured logging (DevOps practice)

```json
{"level":"info","msg":"deploy complete","service":"api","version":"abc1234"}
```

Parse with `| json` — avoids regex fragility.

---

## Lab

1. Generate nginx access logs: `for i in $(seq 1 20); do curl -s http://localhost:8080/ > /dev/null; done`
2. In Grafana Explore (Loki), find `handbook-demo-app` container logs.
3. Filter lines containing `GET`.
4. Add Loki panel to your Day 3 dashboard.
5. Stop demo-app, trigger `up` or blackbox alert (Day 4), find correlated log gap.

---

## Day 5 checklist

- [ ] Loki and Promtail healthy
- [ ] Ran LogQL label selectors
- [ ] Correlated metric spike with logs
- [ ] Understand label-first indexing

**Next:** [Day 6 — Exporters & probes](../day6/)
