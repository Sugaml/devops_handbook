# Day 3 — Pods: Lifecycle, Multi-Container & Debugging

**Goal:** Understand Pod as the atomic unit, container states, restart policies, multi-container patterns, and practical debugging workflows.

**Time:** 5–6 hours

---

## 1. Pod lifecycle phases

| Phase | Meaning |
|-------|---------|
| `Pending` | Accepted, not yet running (scheduling, image pull) |
| `Running` | At least one container running |
| `Succeeded` | All containers terminated successfully |
| `Failed` | At least one container failed |
| `Unknown` | Node communication lost |

```bash
kubectl get pod -n handbook-lab -w
kubectl describe pod POD_NAME -n handbook-lab   # Events section is gold
```

### Container states

- **Waiting** — e.g. `ContainerCreating`, `ImagePullBackOff`, `CrashLoopBackOff`
- **Running**
- **Terminated** — exit code and reason

---

## 2. Restart policies

```yaml
spec:
  restartPolicy: Always   # default for Deployments
  # Never | OnFailure
```

| Policy | Use case |
|--------|----------|
| `Always` | Long-running services (via Deployment) |
| `OnFailure` | Jobs, batch |
| `Never` | Debugging, one-shot tasks |

Bare Pods with `Always` restart on node/kubelet restart; use **Deployments** for production (Day 5).

---

## 3. Single-container Pod manifest

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: api-v1
  namespace: handbook-lab
  labels:
    app: api
    version: v1
spec:
  containers:
    - name: api
      image: hashicorp/http-echo:1.0
      args:
        - "-text=Hello from Pod"
        - "-listen=:8080"
      ports:
        - containerPort: 8080
          name: http
      resources:
        requests:
          cpu: 100m
          memory: 64Mi
        limits:
          memory: 128Mi
```

```bash
kubectl apply -f manifests/api-pod.yaml
kubectl port-forward pod/api-v1 8080:8080 -n handbook-lab
curl localhost:8080
```

---

## 4. Multi-container Pods

### Sidecar pattern (preview — full treatment Day 21)

```yaml
spec:
  containers:
    - name: app
      image: nginx:1.27-alpine
      volumeMounts:
        - name: logs
          mountPath: /var/log/nginx
    - name: log-shipper
      image: busybox:1.36
      command: ["sh", "-c", "tail -F /var/log/nginx/access.log"]
      volumeMounts:
        - name: logs
          mountPath: /var/log/nginx
  volumes:
    - name: logs
      emptyDir: {}
```

Containers in a Pod share `localhost` networking — `127.0.0.1:PORT` reaches sibling containers.

---

## 5. Environment variables

```yaml
env:
  - name: APP_ENV
    value: staging
  - name: POD_NAME
    valueFrom:
      fieldRef:
        fieldPath: metadata.name
  - name: NODE_NAME
    valueFrom:
      fieldRef:
        fieldPath: spec.nodeName
```

```bash
kubectl exec api-v1 -n handbook-lab -- env | sort
```

---

## 6. Debugging toolkit

```bash
# Logs
kubectl logs api-v1 -n handbook-lab
kubectl logs api-v1 -n handbook-lab --previous    # crashed container
kubectl logs api-v1 -c CONTAINER -n handbook-lab  # multi-container

# Interactive debug
kubectl exec -it api-v1 -n handbook-lab -- sh
kubectl debug node/NODE_NAME -it --image=busybox   # node shell (K8s 1.23+)

# Ephemeral debug container (K8s 1.23+)
kubectl debug -it api-v1 -n handbook-lab --image=busybox --target=api -- sh

# Copy files
kubectl cp handbook-lab/api-v1:/etc/nginx/nginx.conf ./nginx.conf

# Events cluster-wide
kubectl get events -n handbook-lab --sort-by='.lastTimestamp'
```

### Common failure modes

| Symptom | Likely cause | Check |
|---------|--------------|-------|
| `ImagePullBackOff` | Wrong tag, private registry auth | `describe pod`, imagePullSecrets |
| `CrashLoopBackOff` | App exits immediately | `logs --previous`, command/args |
| `Pending` | Insufficient resources, taints | `describe pod`, `describe node` |
| `CreateContainerConfigError` | Missing ConfigMap/Secret | `describe pod` |

---

## 7. Pod QoS preview (Day 10 deep dive)

- **Guaranteed** — limits = requests for all containers
- **Burstable** — requests set, limits may differ
- **BestEffort** — no requests/limits

```bash
kubectl get pod api-v1 -n handbook-lab -o jsonpath='{.status.qosClass}'
```

---

## 8. Lab — Day 3

1. Deploy `api-v1` Pod from section 3; port-forward and curl it.
2. Break it on purpose: change image to `nginx:does-not-exist`; observe events; fix image.
3. Create a Pod that exits immediately (`command: ["sh","-c","exit 1"]`) with `restartPolicy: OnFailure`; watch restarts.
4. Build a two-container Pod (nginx + busybox tailing logs); verify shared volume.
5. Practice `kubectl logs --previous` after a crash.
6. Document your personal **debug checklist** (5 commands) in your notes.

**Stretch:** Use `kubectl run debug --rm -it --restart=Never --image=nicolaka/netshoot -n handbook-lab -- bash` for network troubleshooting tools.

---

## 9. DevOps connections

- **Never run naked Pods in prod** — Deployments add self-healing and rollouts.
- **12-factor config:** Env vars from ConfigMaps/Secrets (Days 8–9), not baked in images.
- **Observability:** Logs go to stdout; sidecars/agents collect them (Day 25).

---

## Quick reference

| Task | Command |
|------|---------|
| Pod events | `kubectl describe pod NAME` |
| Previous logs | `kubectl logs NAME --previous` |
| Local access | `kubectl port-forward pod/NAME LOCAL:REMOTE` |
| QoS class | `-o jsonpath='{.status.qosClass}'` |

**Next:** [Day 4 — Labels & selectors](../day4/)
