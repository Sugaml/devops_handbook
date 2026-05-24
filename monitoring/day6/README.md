# Day 6 — Exporters, Blackbox Probes & Service Discovery

**Goal:** Monitor endpoints you do not control, use blackbox probing, and understand static vs dynamic scrape configs.

**Time:** 4–5 hours

---

## 1. Exporter pattern

Applications expose business metrics; **exporters** translate system state to Prometheus format:

| Exporter | Targets |
|----------|---------|
| `node-exporter` | Host CPU, disk, memory |
| `postgres-exporter` | DB stats |
| `redis-exporter` | Redis INFO metrics |
| `nginx-prometheus-exporter` | Stub status page |

Pattern: sidecar or adjacent process, single `/metrics` port.

---

## 2. Blackbox exporter

Probes **from outside** — HTTP, TCP, ICMP, DNS:

```promql
probe_success{job="blackbox_http"}
probe_http_duration_seconds{job="blackbox_http"}
```

Lab config: `labs/blackbox/blackbox.yml`, scrape job in `prometheus.yml`.

Relabeling turns `http://demo-app:80/` into probe target — study **Prometheus → Status → Configuration** for the `blackbox_http` job.

---

## 3. Service discovery (concepts)

| Mechanism | When |
|-----------|------|
| `static_configs` | Labs, tiny fleets |
| `dns_sd_configs` | Consul, internal DNS |
| `kubernetes_sd_configs` | Pods with scrape annotations |
| `ec2_sd_configs` | AWS ASG instances |

Example annotation on a Pod:

```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
```

---

## 4. `metric_relabel_configs` vs `relabel_configs`

- **relabel_configs** — before scrape (target discovery)
- **metric_relabel_configs** — after scrape (drop expensive series)

Drop high-cardinality in production:

```yaml
metric_relabel_configs:
  - source_labels: [__name__]
    regex: go_gc_duration_seconds.*
    action: drop
```

---

## Lab

1. Query `probe_success` and `probe_http_duration_seconds` — confirm demo app healthy.
2. Stop demo-app: `docker stop handbook-demo-app` — watch `probe_success` drop.
3. Add a second blackbox target `http://prometheus:9090/-/healthy` in `prometheus.yml`, reload.
4. List three exporters you would deploy for a stack running Postgres + Redis + nginx (names only).
5. Read one `kubernetes_sd_configs` example in [Prometheus docs](https://prometheus.io/docs/prometheus/latest/configuration/configuration/).

---

## Day 6 checklist

- [ ] Interpreted blackbox metrics
- [ ] Understand relabeling flow
- [ ] Know SD options for K8s and cloud
- [ ] Simulated probe failure

**Next:** [Day 7 — SLOs & capstone](../day7/)
