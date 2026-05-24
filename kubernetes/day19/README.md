# Day 19 — Liveness, Readiness & Startup Probes

**Goal:** Configure health checks so Kubernetes routes traffic correctly, restarts truly unhealthy containers, and handles slow-start apps.

**Time:** 4–5 hours

---

## 1. Three probe types

| Probe | Fails when | Kubelet action |
|-------|------------|----------------|
| **Liveness** | App deadlocked/hung | Restart container |
| **Readiness** | Not ready for traffic | Remove from Service endpoints |
| **Startup** | Still starting | Disable other probes until success |

**Golden rule:** Readiness = traffic gate. Liveness = restart gate. Don't put dependency checks on liveness.

---

## 2. HTTP probe example

```yaml
spec:
  containers:
    - name: api
      image: myapp:1.0
      ports:
        - containerPort: 8080
      readinessProbe:
        httpGet:
          path: /ready
          port: 8080
        initialDelaySeconds: 5
        periodSeconds: 10
        failureThreshold: 3
      livenessProbe:
        httpGet:
          path: /healthz
          port: 8080
        initialDelaySeconds: 15
        periodSeconds: 20
      startupProbe:
        httpGet:
          path: /healthz
          port: 8080
        failureThreshold: 30
        periodSeconds: 10
```

---

## 3. Probe mechanisms

```yaml
# TCP socket
readinessProbe:
  tcpSocket:
    port: 5432

# Exec command
livenessProbe:
  exec:
    command:
      - pg_isready
      - -U
      - postgres
```

---

## 4. Probe timing fields

| Field | Meaning |
|-------|---------|
| `initialDelaySeconds` | Wait before first probe |
| `periodSeconds` | Interval |
| `timeoutSeconds` | Probe timeout |
| `successThreshold` | Consecutive successes to mark healthy |
| `failureThreshold` | Failures before action |

Startup probe: `failureThreshold × periodSeconds` = max startup time.

---

## 5. Common mistakes

| Mistake | Symptom |
|---------|---------|
| Liveness hits DB-dependent endpoint | Restart loop during DB outage |
| Readiness same as liveness on `/` | Traffic to half-ready app |
| No startup probe on slow JVM | Liveness kills during boot |
| Probe too aggressive | Flapping under load |

---

## 6. Testing with nginx

```yaml
readinessProbe:
  httpGet:
    path: /
    port: 80
livenessProbe:
  httpGet:
    path: /
    port: 80
```

Break readiness: mount broken config; watch endpoints drain.

```bash
kubectl get endpoints web -n handbook-lab -w
kubectl describe pod -n handbook-lab | grep -A10 "Conditions"
```

---

## 7. Lab — Day 19

1. Add readiness + liveness to Day 5 `web` Deployment.
2. During rollout, watch endpoints — ready count should increase gradually.
3. Exec into pod and break nginx config; observe liveness restart.
4. Deploy app with 60s sleep before listening; add startupProbe; verify no premature liveness kill.
5. Create Pod with failing readiness (`path: /nope`); confirm Service returns no endpoints.

**Stretch:** Implement `/ready` that checks Redis connectivity; fail readiness when Redis down only.

---

## 8. DevOps connections

- **Rolling updates:** `maxUnavailable` + readiness = zero-downtime requirement.
- **Load tests:** Probes must tolerate latency spikes — tune thresholds.
- **gRPC:** Use `grpc` probe type (K8s 1.24+) or exec grpc_health_probe.

---

## Quick reference

| Task | Command |
|------|---------|
| Probe status | `kubectl describe pod` → Conditions |
| Endpoints | `kubectl get endpoints` |
| Restart count | `kubectl get pod` RESTARTS column |
| Startup max time | `failureThreshold * periodSeconds` |

**Next:** [Day 20 — Autoscaling](../day20/)
