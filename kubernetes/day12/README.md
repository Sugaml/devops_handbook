# Day 12 — DaemonSets, Jobs & CronJobs

**Goal:** Run one Pod per node (DaemonSet), batch work to completion (Job), and scheduled batch (CronJob).

**Time:** 4–5 hours

---

## 1. DaemonSet

Ensures a Pod runs on every (matching) node — logging agents, CNI, node-exporter.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-logger
  namespace: handbook-lab
spec:
  selector:
    matchLabels:
      app: node-logger
  template:
    metadata:
      labels:
        app: node-logger
    spec:
      tolerations:
        - operator: Exists   # often needed for control-plane nodes
      containers:
        - name: logger
          image: busybox:1.36
          command: ["sh", "-c", "while true; do date >> /var/log/node.log; sleep 60; done"]
          volumeMounts:
            - name: varlog
              mountPath: /var/log
      volumes:
        - name: varlog
          hostPath:
            path: /var/log
```

```bash
kubectl get ds -n handbook-lab
kubectl get pods -n handbook-lab -l app=node-logger -o wide   # one per node
```

---

## 2. Job — run to completion

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: pi-calc
  namespace: handbook-lab
spec:
  completions: 1
  parallelism: 1
  backoffLimit: 3
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: pi
          image: perl:5.36
          command: ["perl", "-Mbignum=b", "-wle", "print bpi(2000)"]
```

```bash
kubectl apply -f job.yaml
kubectl get jobs -n handbook-lab
kubectl logs job/pi-calc -n handbook-lab
kubectl wait --for=condition=complete job/pi-calc -n handbook-lab --timeout=120s
```

### Indexed & parallel Jobs

```yaml
spec:
  completions: 5
  parallelism: 2
  completionMode: Indexed
```

---

## 3. CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: hello-cron
  namespace: handbook-lab
spec:
  schedule: "*/5 * * * *"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: hello
              image: busybox:1.36
              command: ["sh", "-c", "echo Hello at $(date)"]
```

```bash
kubectl get cronjobs -n handbook-lab
kubectl get jobs -n handbook-lab   # spawned by CronJob
```

Cron uses standard cron syntax (minute hour dom month dow).

---

## 4. Cleanup

```bash
kubectl delete job pi-calc -n handbook-lab
kubectl delete cronjob hello-cron -n handbook-lab
# TTL controller auto-delete (K8s 1.23+)
spec:
  ttlSecondsAfterFinished: 100
```

---

## 5. Lab — Day 12

1. Deploy DaemonSet; confirm pod count equals node count.
2. Run Job `pi-calc`; wait for completion; capture logs.
3. Create CronJob every minute (`* * * * *`); watch Jobs spawn; delete after verification.
4. Create failing Job (`exit 1`); observe `backoffLimit` retries.
5. Add `ttlSecondsAfterFinished: 60` to Job; verify auto cleanup.

**Stretch:** Taint a node; add matching toleration to DaemonSet only.

---

## 6. DevOps connections

- **CI:** One-off migration Jobs common in deploy pipelines.
- **Security:** DaemonSets with hostPath are high privilege — restrict RBAC.
- **Alternatives:** External schedulers (Airflow, Jenkins) for complex DAGs.

---

## Quick reference

| Task | Command |
|------|---------|
| Job status | `kubectl get jobs` |
| CronJob | `kubectl get cronjobs` |
| Job logs | `kubectl logs job/NAME` |
| Wait complete | `kubectl wait --for=condition=complete job/NAME` |

**Next:** [Day 13 — RBAC](../day13/)
