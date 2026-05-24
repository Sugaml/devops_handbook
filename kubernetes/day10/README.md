# Day 10 — Requests, Limits, QoS & ResourceQuota

**Goal:** Define CPU/memory requests and limits, understand QoS classes and eviction, and enforce namespace quotas and limit ranges.

**Time:** 5 hours

---

## 1. Why resource management?

| Without limits | With requests/limits |
|----------------|----------------------|
| Noisy neighbor eats node RAM | Scheduler places Pods predictably |
| OOM kills random processes | Container OOMKilled at limit |
| Cannot capacity plan | Cluster autoscaler has signals |

---

## 2. CPU and memory units

| Resource | Request/limit unit | Notes |
|----------|-------------------|-------|
| **CPU** | `500m` = 0.5 core, `2` = 2 cores | Compressible; throttled not killed |
| **Memory** | `256Mi`, `1Gi` | Not compressible; exceed limit → OOMKill |

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 256Mi
```

---

## 3. QoS classes

| Class | Condition | Eviction priority |
|-------|-----------|-------------------|
| **Guaranteed** | limits = requests for all containers (cpu/mem) | Last evicted |
| **Burstable** | At least one request set | Middle |
| **BestEffort** | No requests/limits | First evicted |

```bash
kubectl get pod NAME -o jsonpath='{.status.qosClass}'
```

---

## 4. Namespace ResourceQuota

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: handbook-lab
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "20"
```

```bash
kubectl apply -f resourcequota.yaml
kubectl describe resourcequota compute-quota -n handbook-lab
```

---

## 5. LimitRange (defaults)

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: handbook-lab
spec:
  limits:
    - default:
        cpu: 500m
        memory: 256Mi
      defaultRequest:
        cpu: 100m
        memory: 128Mi
      type: Container
```

Pods without explicit resources inherit defaults.

---

## 6. Monitoring usage

```bash
kubectl top nodes    # requires metrics-server
kubectl top pods -n handbook-lab

# Install metrics-server on kind (often needed)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
# kind: may need --kubelet-insecure-tls arg patch
```

---

## 7. OOM and CPU throttling

```bash
# OOMKilled
kubectl describe pod NAME | grep -A5 "Last State"

# CPU throttling (needs metrics/cAdvisor)
# High throttling → increase cpu limit or optimize app
```

---

## 8. Lab — Day 10

1. Install metrics-server on your cluster (patch for kind if needed).
2. Deploy Pod with `requests.memory: 64Mi`, `limits.memory: 64Mi`; run stress (optional: `stress-ng`) and observe OOM.
3. Apply ResourceQuota limiting `pods: 5`; try to exceed it.
4. Apply LimitRange; create Pod without resources; verify defaults injected.
5. Compare QoS for BestEffort vs Burstable vs Guaranteed pods.

**Stretch:** Set `requests.cpu` sum near node capacity; observe Pending pods with `Insufficient cpu`.

---

## 9. DevOps connections

- **Cost:** Requests drive billing on some platforms; limits drive burst capacity.
- **VPA** (Day 20) recommends requests; don't set and forget.
- **Java/Node apps:** Heap must fit inside memory limit — common production failure.

---

## Quick reference

| Task | Command |
|------|---------|
| Pod usage | `kubectl top pod -n NS` |
| QoS | `-o jsonpath='{.status.qosClass}'` |
| Quota status | `kubectl describe resourcequota -n NS` |
| CPU unit | `1000m` = 1 core |

**Next:** [Day 11 — StatefulSets](../day11/)
