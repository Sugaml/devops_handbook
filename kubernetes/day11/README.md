# Day 11 — StatefulSets & Stable Identity

**Goal:** Run stateful workloads with stable network identity, ordered deployment, and persistent storage per replica.

**Time:** 5–6 hours

---

## 1. Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod names | Random suffix | Ordered, stable (`web-0`, `web-1`) |
| Network identity | Random | Stable DNS per pod |
| Storage | Shared or none | Dedicated PVC per replica (typical) |
| Scale order | Parallel | Ordered create/delete |
| Use case | Stateless HTTP | Databases, Kafka, ZooKeeper |

---

## 2. StatefulSet manifest

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
  namespace: handbook-lab
spec:
  serviceName: web-headless
  replicas: 3
  selector:
    matchLabels:
      app: web
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
          volumeMounts:
            - name: data
              mountPath: /usr/share/nginx/html
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 1Gi
```

Requires **headless Service** `web-headless` (Day 6).

---

## 3. Stable DNS

Pod DNS name:

```
<pod-name>.<service-name>.<namespace>.svc.cluster.local
web-0.web-headless.handbook-lab.svc.cluster.local
web-1.web-headless.handbook-lab.svc.cluster.local
```

```bash
kubectl run dns-test --rm -it --restart=Never --image=busybox:1.36 -n handbook-lab -- \
  nslookup web-0.web-headless.handbook-lab.svc.cluster.local
```

---

## 4. Ordered operations

```bash
kubectl scale statefulset web --replicas=5 -n handbook-lab   # web-3, web-4 created in order
kubectl delete pod web-2 -n handbook-lab                     # recreated as web-2
kubectl rollout restart statefulset web -n handbook-lab      # reverse ordinal delete/create
```

---

## 5. Updates

```yaml
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2   # only pods with ordinal >= 2 update (canary by ordinal)
```

`OnDelete` strategy — manual pod delete triggers update.

---

## 6. Lab — Day 11

1. Create headless Service `web-headless` selecting `app: web`.
2. Deploy StatefulSet with 3 replicas and volumeClaimTemplates (use default StorageClass).
3. Write unique `index.html` per pod via exec; verify persistence after pod delete.
4. Scale to 4; resolve DNS for `web-3`.
5. Set `partition: 2`; update image; observe only web-2+ change.

**Stretch:** Deploy single-replica PostgreSQL StatefulSet (official chart or minimal manifest) — backup Day 24.

---

## 7. DevOps connections

- **Operators** (Day 22) automate StatefulSet ops for databases.
- **Anti-pattern:** Running primary DB without backups or PodDisruptionBudget.
- **ReadWriteOnce:** One node at a time — affects multi-AZ scheduling.

---

## Quick reference

| Task | Command |
|------|---------|
| List STS | `kubectl get sts -n handbook-lab` |
| Pod DNS | `<pod>.<headless-svc>.<ns>.svc.cluster.local` |
| Scale | `kubectl scale sts NAME --replicas=N` |
| PVCs | `kubectl get pvc -n handbook-lab` |

**Next:** [Day 12 — DaemonSets, Jobs & CronJobs](../day12/)
