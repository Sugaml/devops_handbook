# Day 3 — Grafana: Dashboards, Variables & Explore

**Goal:** Build and refine dashboards, use template variables, and correlate metrics in Explore.

**Time:** 4–5 hours

---

## 1. Grafana data model

```
Datasource (Prometheus) → Panel queries → Dashboard → Folder
```

Provisioned datasources live in `labs/grafana/provisioning/datasources/`. Dashboards can be UI-built or JSON under `provisioning/dashboards/json/`.

---

## 2. Explore vs Dashboard

| Mode | Best for |
|------|----------|
| **Explore** | Ad-hoc debugging, sharing query links |
| **Dashboard** | Persistent views for team / on-call |

Open **Explore → Prometheus** and paste PromQL from Day 2.

---

## 3. Build a panel

1. **Dashboards → New → New dashboard → Add visualization**
2. Datasource: **Prometheus**
3. Query: `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
4. Panel type: **Time series**
5. Unit: **Percent (0–100)**
6. Legend: `{{instance}}`

Save to folder **Handbook**.

---

## 4. Template variables

Add variable `instance`:

- Type: **Query**
- Query: `label_values(up{job="node"}, instance)`

Use in panel:

```promql
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle", instance=~"$instance"}[5m])) * 100)
```

Multi-select + **All** option teaches dynamic dashboards without copy-paste.

---

## 5. Annotations & links

- **Annotations** — mark deploy times (API or manual) to correlate spikes.
- **Data links** — jump from panel to Loki logs (Day 5) with shared labels.

---

## Lab

1. Import or extend **Handbook — Node Overview** with a disk usage panel:

```promql
100 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} * 100)
```

2. Add `instance` template variable.
3. Create a **Stat** panel for `count(up == 1)` — total healthy targets.
4. Export dashboard JSON to `day3/labs/my-dashboard.json` (backup only; optional commit).
5. Share an Explore URL with a teammate (or future you) with time range and query encoded.

---

## Day 3 checklist

- [ ] Built a panel with correct units
- [ ] Added a template variable
- [ ] Used Explore for ad-hoc queries
- [ ] Understand provisioning vs UI dashboards

**Next:** [Day 4 — Alerting](../day4/)
