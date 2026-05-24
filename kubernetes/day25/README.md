# Day 25 — Observability: Metrics, Logs & Traces

**Goal:** Implement the three pillars of observability on Kubernetes — Prometheus metrics, centralized logging, and distributed tracing basics.

**Time:** 6 hours

---

## 1. Observability stack overview

```
Apps (metrics/logs/traces)
    │
    ├── Prometheus / kube-prometheus-stack → Grafana
    ├── Loki / EFK / CloudWatch Container Insights
    └── Jaeger / Tempo / OpenTelemetry Collector
```

---

## 2. Metrics with kube-prometheus-stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

kubectl get pods -n monitoring
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
# default user admin / get password from secret
```

Key metrics:

- `container_cpu_usage_seconds_total`
- `container_memory_working_set_bytes`
- `kube_pod_status_phase`
- HTTP RED: Rate, Errors, Duration

---

## 3. ServiceMonitor (Prometheus Operator)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: web
  namespace: handbook-lab
  labels:
    release: monitoring
spec:
  selector:
    matchLabels:
      app: web
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
```

App must expose `/metrics` in Prometheus format.

---

## 4. Logging architecture

| Approach | Components |
|----------|------------|
| **Node agent** | Fluent Bit / Fluentd DaemonSet → Loki/ES |
| **Sidecar** | App log file + sidecar shipper |
| **Stdout** | Preferred — container logs to stdout/stderr |

```bash
kubectl logs -f deployment/web -n handbook-lab
kubectl logs deployment/web -n handbook-lab --since=1h --timestamps
```

Central query (Loki example):

```bash
# LogQL in Grafana: {namespace="handbook-lab", app="web"}
```

---

## 5. Tracing with OpenTelemetry

Instrument app with OTel SDK → export to Collector → Jaeger/Tempo.

```yaml
env:
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    value: http://otel-collector.monitoring:4317
  - name: OTEL_SERVICE_NAME
    value: web
```

Kubernetes adds resource attributes: `k8s.pod.name`, `k8s.namespace.name`.

---

## 6. kubectl debugging observability

```bash
kubectl top nodes
kubectl top pods -n handbook-lab
kubectl get --raw /metrics | head
kubectl get events -A --sort-by='.lastTimestamp' | tail -20
```

---

## 7. Lab — Day 25

1. Install kube-prometheus-stack (or prometheus + grafana minimally).
2. Open Grafana; import dashboard ID 315 (Kubernetes cluster monitoring) or built-in views.
3. Query CPU usage for `handbook-lab` namespace in Prometheus UI.
4. Deploy app with `nginx-prometheus-exporter` sidecar or sample metrics app.
5. Tail logs from two replicas simultaneously with stern (optional): `stern web -n handbook-lab`.

**Stretch:** Deploy Loki stack and correlate logs with Grafana Explore.

---

## 8. DevOps connections

- **SLOs/SLIs:** Error budget alerts from Prometheus (Alertmanager).
- **Cost:** Long log retention expensive — sample and tier storage.
- **On-call:** Runbooks link Grafana dashboards + log queries + trace IDs.

---

## Quick reference

| Task | Command |
|------|---------|
| Pod metrics | `kubectl top pod -n NS` |
| Logs follow | `kubectl logs -f deploy/NAME` |
| Grafana PF | `kubectl port-forward svc/grafana 3000:80` |
| Events | `kubectl get events -n NS --sort-by=...` |

**Next:** [Day 26 — Security](../day26/)
