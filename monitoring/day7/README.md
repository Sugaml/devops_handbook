# Day 7 — SLOs, On-Call Runbooks & Capstone

**Goal:** Define SLIs/SLOs, assemble an incident playbook, and run a simulated outage across metrics, logs, and alerts.

**Time:** 5–6 hours

---

## 1. SLI, SLO, SLA

| Term | Definition |
|------|------------|
| **SLI** | Measurable indicator (availability, latency, error rate) |
| **SLO** | Target for SLI (99.9% availability / 30d) |
| **SLA** | Contract with customer consequences |

Example SLI — availability:

```promql
sum(rate(http_requests_total{status!~"5.."}[5m]))
/
sum(rate(http_requests_total[5m]))
```

Error budget = allowed unreliability before SLO breach.

---

## 2. RED and USE methods

| Method | Scope | Metrics |
|--------|-------|---------|
| **USE** | Resources | Utilization, Saturation, Errors |
| **RED** | Services | Rate, Errors, Duration |

Map alerts to methods — avoid alerting on every CPU blip without customer impact.

---

## 3. On-call runbook template

```markdown
## Alert: HandbookTargetDown

**Impact:** Host metrics missing; may mask disk/memory incidents.

**Verify:**
1. Prometheus → Targets → job=node
2. SSH / docker ps on node-exporter host

**Mitigate:**
1. Restart node-exporter
2. Check firewall :9100

**Escalate:** platform team if >3 nodes
```

Store in wiki; link from `annotations.runbook_url`.

---

## 4. Incident simulation (capstone)

**Scenario:** Demo app slow + errors.

1. Baseline: all targets UP, blackbox `probe_success==1`.
2. Break: `docker pause handbook-demo-app` or flood with `ab -n 1000 -c 50 http://localhost:8080/`.
3. Detect: Grafana dashboard + `probe_http_duration_seconds` + Loki 5xx/access errors.
4. Alert: confirm firing or manually note threshold breach.
5. Mitigate: unpause / scale / restart.
6. Post-incident: write 5-bullet postmortem (timeline, root cause, action items).

---

## 5. Production checklist

- [ ] Retention and remote write sized for compliance
- [ ] Alert routes tested quarterly (pager drill)
- [ ] Dashboards version-controlled (GitOps)
- [ ] Cardinality review on top 10 metrics
- [ ] Secrets in Alertmanager via env / vault, not git
- [ ] kube-prometheus-stack or AMP for Kubernetes fleets

---

## Lab

Complete capstone simulation above. Deliverable: `day7/labs/incident_report.md` with:

1. Timeline (UTC)
2. Graphs/screenshots described in text
3. PromQL and LogQL used
4. One preventive action (better alert, runbook, or instrumentation)

---

## Day 7 checklist

- [ ] Defined one SLI and SLO for a fictional API
- [ ] Completed incident simulation
- [ ] Wrote runbook section for one alert
- [ ] Finished capstone report

**Track complete.** Extend with [Kubernetes](../kubernetes/) ServiceMonitors or cloud-native managed Prometheus.
