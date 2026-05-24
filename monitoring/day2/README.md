# Day 2 — PromQL: Rates, Aggregations & Debugging

**Goal:** Write production-useful PromQL for counters and gauges, aggregate by labels, and debug empty query results.

**Time:** 4–5 hours

---

## 1. Selectors and matchers

```promql
node_memory_MemAvailable_bytes{instance="node-exporter:9100"}
node_cpu_seconds_total{mode!="idle"}
{__name__=~"node_memory_.*"}
```

| Matcher | Meaning |
|---------|---------|
| `=` | Exact label match |
| `!=` | Not equal |
| `=~` | Regex match |
| `!~` | Regex not match |

---

## 2. `rate()` vs `irate()`

Counters only go up (or reset to 0 on restart). Always use `rate()` or `increase()` over a range:

```promql
# 5m average per-second rate — use for alerts and dashboards
rate(node_network_receive_bytes_total[5m])

# Instant rate — spiky; good for graphs, risky for alerts
irate(node_network_receive_bytes_total[5m])
```

**Rule:** Alerts and SLOs → `rate(...[5m])` or longer window.

---

## 3. Aggregations

```promql
# CPU % by instance (non-idle modes)
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Total network RX across all interfaces
sum(rate(node_network_receive_bytes_total[5m]))

# Top 3 instances by memory pressure
topk(3, 1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)
```

| Function | Use |
|----------|-----|
| `sum`, `avg`, `min`, `max` | Roll up labels |
| `by (label)` | Keep label dimensions |
| `without (label)` | Drop label from grouping |
| `count` | Number of series |

---

## 4. Histograms (intro)

When apps expose histograms:

```promql
histogram_quantile(0.99,
  sum by (le) (rate(http_request_duration_seconds_bucket[5m]))
)
```

Requires `_bucket`, `_sum`, `_count` series from instrumentation.

---

## 5. Cardinality trap

**Bad:** `http_requests_total{user_id="12345"}` — millions of series, OOM Prometheus.

**Good:** `http_requests_total{route="/api/orders", status="500"}` — bounded labels.

---

## Lab

1. Compute **CPU utilization %** per instance (formula from Day 1).
2. Graph **memory available %** over 15 minutes in Grafana Explore.
3. Use `topk` to find highest `node_filesystem_avail_bytes` consumer mount.
4. Break a query on purpose (wrong label) — use **Explain** tab in Prometheus UI.
5. Document three labels on `node_cpu_seconds_total` and what each means.

---

## Day 2 checklist

- [ ] Used `rate` with a range vector
- [ ] Used `sum` / `avg` with `by`
- [ ] Understand cardinality risk
- [ ] Completed Grafana Explore exercise

**Next:** [Day 3 — Grafana](../day3/)
