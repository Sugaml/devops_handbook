# Day 5 — Deployments & Rolling Updates

**Goal:** Run stateless apps with Deployments, understand ReplicaSets, perform rolling updates and rollbacks, and control surge/unavailability.

**Time:** 5–6 hours

---

## 1. Deployment → ReplicaSet → Pods

```
Deployment (desired state: 3 replicas, image v2)
    └── ReplicaSet (revision 2) → 3 Pods
    └── ReplicaSet (revision 1) → 0 Pods (scaled down, kept for rollback)
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: handbook-lab
  labels:
    app: web
spec:
  replicas: 3
  revisionHistoryLimit: 5
  selector:
    matchLabels:
      app: web
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: nginx
          image: nginx:1.27-alpine
          ports:
            - containerPort: 80
```

```bash
kubectl apply -f manifests/web-deployment.yaml
kubectl get deploy,rs,pods -n handbook-lab -l app=web
```

---

## 2. Rolling update strategies

| Setting | Meaning |
|---------|---------|
| `maxSurge` | Extra Pods above desired count during rollout |
| `maxUnavailable` | Pods that can be down during rollout |
| `Recreate` strategy | Kill all, then create new (downtime) |

```bash
# Trigger rollout
kubectl set image deployment/web nginx=nginx:1.27-alpine -n handbook-lab
kubectl rollout status deployment/web -n handbook-lab

# Watch ReplicaSets
kubectl get rs -n handbook-lab -l app=web -w
```

---

## 3. Rollback and history

```bash
kubectl rollout history deployment/web -n handbook-lab
kubectl rollout history deployment/web --revision=2 -n handbook-lab

kubectl rollout undo deployment/web -n handbook-lab
kubectl rollout undo deployment/web --to-revision=1 -n handbook-lab

# Pause/resume (canary manual gate)
kubectl rollout pause deployment/web -n handbook-lab
kubectl rollout resume deployment/web -n handbook-lab
```

Record change cause:

```bash
kubectl annotate deployment/web kubernetes.io/change-cause="upgrade nginx 1.27" --overwrite -n handbook-lab
```

---

## 4. Scaling

```bash
kubectl scale deployment web --replicas=5 -n handbook-lab
kubectl autoscale deployment web --min=2 --max=10 --cpu-percent=70 -n handbook-lab  # HPA Day 20
```

---

## 5. Deployment gotchas

| Issue | Cause | Fix |
|-------|-------|-----|
| Rollout stuck | Readiness probe failing | Check pods, probes (Day 19) |
| Old RS not scaling down | `maxUnavailable` + surge math | Adjust strategy |
| Selector immutable error | Changed `matchLabels` | New Deployment name |
| `ProgressDeadlineExceeded` | Pods not becoming ready | `describe deploy`, events |

---

## 6. Zero-downtime pattern checklist

1. Readiness probe passes before Pod receives traffic (Day 19).
2. `maxUnavailable: 0` for critical services.
3. PodDisruptionBudget for voluntary evictions (Day 24).
4. PreStop hook for graceful shutdown (optional):

```yaml
lifecycle:
  preStop:
    exec:
      command: ["/bin/sh", "-c", "sleep 5"]
```

---

## 7. Lab — Day 5

1. Deploy `web` with 3 replicas.
2. Update image to a different tag; watch rollout with `kubectl rollout status`.
3. Break rollout: set image to invalid tag; observe; rollback with `kubectl rollout undo`.
4. Scale to 5, then to 1; observe ReplicaSet behavior.
5. Export deployment YAML after two revisions; count ReplicaSets.
6. Set `maxSurge: 0`, `maxUnavailable: 1`; repeat update and note difference in pod churn.

**Stretch:** Use `kubectl patch deployment web -n handbook-lab -p '{"spec":{"template":{"spec":{"containers":[{"name":"nginx","image":"nginx:1.26-alpine"}]}}}}'`.

---

## 8. DevOps connections

- **CI/CD:** Pipeline updates image tag in manifest or Helm values; cluster reconciles.
- **Blue/green & canary:** Argo Rollouts, Flagger, or manual weighted Services — Day 23 GitOps ties in.
- **Immutable tags:** Prefer digest `@sha256:...` over `:latest` in production.

---

## Quick reference

| Task | Command |
|------|---------|
| Update image | `kubectl set image deploy/NAME c=IMAGE` |
| Rollout status | `kubectl rollout status deploy/NAME` |
| Undo | `kubectl rollout undo deploy/NAME` |
| History | `kubectl rollout history deploy/NAME` |

**Next:** [Day 6 — Services](../day6/)
