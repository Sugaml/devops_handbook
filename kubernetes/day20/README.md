# Day 20 — HPA, VPA & Cluster Autoscaling

**Goal:** Scale workloads horizontally with HPA, understand VPA and cluster autoscaler, and configure metrics-based scaling.

**Time:** 5 hours

---

## 1. Horizontal Pod Autoscaler (HPA)

Scales Deployment/StatefulSet replicas based on metrics.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web
  namespace: handbook-lab
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

```bash
kubectl apply -f hpa.yaml
kubectl get hpa -n handbook-lab
kubectl describe hpa web -n handbook-lab
```

Requires **metrics-server** (Day 10) and **requests** set on containers.

---

## 2. Imperative HPA

```bash
kubectl autoscale deployment web --cpu-percent=70 --min=2 --max=10 -n handbook-lab
```

---

## 3. Custom metrics

```yaml
metrics:
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
```

Requires Prometheus Adapter or similar metrics API extension.

---

## 4. Scaling behavior (K8s 1.18+)

```yaml
behavior:
  scaleDown:
    stabilizationWindowSeconds: 300
    policies:
      - type: Percent
        value: 50
        periodSeconds: 60
  scaleUp:
    stabilizationWindowSeconds: 0
    policies:
      - type: Pods
        value: 2
        periodSeconds: 60
```

Prevents flapping and aggressive scale-down during traffic dips.

---

## 5. Vertical Pod Autoscaler (VPA)

Adjusts **requests/limits** (and may restart Pods) — not built into all clusters.

```
VPA Recommender → suggests CPU/memory
VPA Updater    → applies (optional auto mode)
```

Use case: right-size requests over time. Often paired with HPA on custom/external metrics.

Install: [kubernetes/autoscaler/tree/master/vertical-pod-autoscaler](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler)

---

## 6. Cluster Autoscaler

Scales **nodes** when Pods are Pending due to insufficient resources.

```
Pending Pod → CA adds node → scheduler places Pod
Underutilized node → CA drains and removes (with PDB respect)
```

Cloud-specific: EKS CA, GKE Autopilot/CA, AKS CA.

---

## 7. Load test HPA

```bash
kubectl run load --rm -it --restart=Never --image=busybox:1.36 -n handbook-lab -- \
  sh -c "while true; do wget -q -O- http://web/handbook-lab; done"

kubectl get hpa -n handbook-lab -w
kubectl get pods -n handbook-lab -l app=web -w
```

Or use `hey`, `kubectl run` with apache bench, etc.

---

## 8. Lab — Day 20

1. Ensure metrics-server works; deploy `web` with cpu requests.
2. Create HPA min=2 max=6 target CPU 50%.
3. Generate load; observe scale up within a few minutes.
4. Stop load; observe scale down (may take stabilization window).
5. Document relationship between requests, actual usage, and HPA percentage.

**Stretch:** Read Prometheus Adapter docs for custom metric HPA.

---

## 9. DevOps connections

- **Cost:** HPA + CA save money vs static oversized fleets.
- **Stateless only:** HPA targets Deployments; databases scale differently.
- **KEDA:** Event-driven scaling (Kafka lag, queue depth) beyond built-in HPA.

---

## Quick reference

| Task | Command |
|------|---------|
| HPA status | `kubectl get hpa -n NS` |
| Create HPA | `kubectl autoscale deploy NAME --cpu-percent=N` |
| Metrics | requires metrics-server + resource requests |
| CA | cloud node pool integration |

**Next:** [Day 21 — Init containers & patterns](../day21/)
