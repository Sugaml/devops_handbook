# Day 4 — Alerting Rules & Alertmanager

**Goal:** Write alerting rules, route notifications through Alertmanager, and practice silences and inhibition.

**Time:** 4–5 hours

---

## 1. Alerting pipeline

```
PromQL rule (fires) → Alertmanager → receiver (Slack, PagerDuty, email)
```

Alerts live in Prometheus `rule_files`; routing in `alertmanager.yml`.

Lab rules: `labs/prometheus/rules/handbook_alerts.yml`.

---

## 2. Rule anatomy

```yaml
- alert: HandbookHighCpu
  expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High CPU on {{ $labels.instance }}"
```

| Field | Purpose |
|-------|---------|
| `expr` | PromQL boolean — true = pending |
| `for` | Must hold true this long before **firing** |
| `labels` | Route/group on these |
| `annotations` | Human-readable context |

Reload after edits:

```bash
curl -X POST http://localhost:9090/-/reload
# or restart prometheus container
```

---

## 3. Alertmanager routing

```yaml
route:
  receiver: handbook-log
  group_by: [alertname, severity]
```

**Grouping** — one notification per incident burst, not per series.

**Inhibition** — critical suppresses warning for same `instance` (see lab config).

---

## 4. Production receivers (patterns)

Replace lab webhook with:

```yaml
receivers:
  - name: slack-oncall
    slack_configs:
      - channel: '#alerts'
        send_resolved: true
```

Use secrets from vault/CI — never commit webhook URLs.

---

## 5. Runbook link in annotations

```yaml
annotations:
  runbook_url: "https://wiki.example.com/runbooks/high-cpu"
```

On-call needs **what to do**, not only **what fired**.

---

## Lab

1. Open **Alertmanager** UI → confirm routing tree matches `alertmanager.yml`.
2. Open **Prometheus → Alerts** — see `HandbookHighCpu` (inactive in idle lab).
3. Temporarily lower CPU threshold in `handbook_alerts.yml` to `> 1`, reload, observe **Pending → Firing**.
4. Create a **Silence** in Alertmanager UI for `alertname=HandbookHighCpu` — confirm notification suppressed.
5. Revert threshold; document when you would use `for: 15m` vs `for: 1m`.

---

## Day 4 checklist

- [ ] Edited and reloaded alerting rules
- [ ] Understand `for` duration
- [ ] Used Alertmanager UI silences
- [ ] Know where to plug real receivers

**Next:** [Day 5 — Logs with Loki](../day5/)
