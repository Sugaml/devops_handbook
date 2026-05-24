# Day 17 — Kubernetes client-python Basics

**Goal:** Use the official Kubernetes Python client to read cluster state, list pods, check deployment readiness, and build small automation scripts that complement `kubectl`.

**Time:** 5–6 hours (theory + hands-on)

---

## 1. client-python vs kubectl

| Approach | Best for |
|----------|----------|
| `kubectl` | Humans, quick ops, GitOps apply |
| **client-python** | Custom controllers, reports, CI gates, integrations |

Both talk to the same **Kubernetes API server**. Python returns structured objects you can filter, aggregate, and feed into dashboards.

```
  ~/.kube/config  ──►  client-python  ──►  API server
                            │
                     CoreV1Api, AppsV1Api, ...
```

---

## 2. Install and load kubeconfig

```bash
pip install kubernetes
kubectl config current-context   # verify access
```

```python
from kubernetes import client, config

# Local development — uses ~/.kube/config
config.load_kube_config()

# In-cluster (pod with ServiceAccount)
# config.load_incluster_config()

v1 = client.CoreV1Api()
pods = v1.list_pod_for_all_namespaces(watch=False)
for pod in pods.items:
    print(pod.metadata.namespace, pod.metadata.name, pod.status.phase)
```

---

## 3. Core API objects

| API class | Resources |
|-----------|-----------|
| `CoreV1Api` | Pods, Services, Namespaces, ConfigMaps |
| `AppsV1Api` | Deployments, StatefulSets, ReplicaSets |
| `BatchV1Api` | Jobs, CronJobs |

```python
apps = client.AppsV1Api()
deployments = apps.list_deployment_for_all_namespaces()
for d in deployments.items:
    desired = d.spec.replicas or 0
    ready = d.status.ready_replicas or 0
    print(d.metadata.namespace, d.metadata.name, f"{ready}/{desired}")
```

---

## 4. Namespace-scoped queries

```python
NS = "handbook-lab"

pods = v1.list_namespaced_pod(namespace=NS)
for p in pods.items:
    containers = [c.name for c in p.spec.containers]
    print(p.metadata.name, p.status.phase, containers)
```

Always scope automation to explicit namespaces — avoid cluster-wide writes unless intentional.

---

## 5. Readiness and rollout status

```python
def deployment_ready(apps, namespace: str, name: str) -> tuple[bool, str]:
    d = apps.read_namespaced_deployment(name, namespace)
    desired = d.spec.replicas or 0
    ready = d.status.ready_replicas or 0
    if ready == desired and desired > 0:
        return True, f"{ready}/{desired} ready"
    return False, f"{ready}/{desired} ready (waiting)"
```

Poll after a deploy (like Day 12 HTTP wait):

```python
import time

def wait_for_deployment(apps, namespace, name, timeout=300):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ok, msg = deployment_ready(apps, namespace, name)
        if ok:
            return True
        time.sleep(5)
    return False
```

---

## 6. Field selectors and labels

```python
pods = v1.list_namespaced_pod(
    namespace="handbook-lab",
    label_selector="app=web",
    field_selector="status.phase=Running",
)
```

Label selectors match `kubectl -l app=web`. Field selectors are more limited but useful for phase filters.

---

## 7. Error handling

```python
from kubernetes.client.rest import ApiException

try:
    v1.read_namespaced_pod("missing", "default")
except ApiException as exc:
    if exc.status == 404:
        print("Pod not found")
    else:
        raise
```

| Status | Meaning |
|--------|---------|
| 401/403 | RBAC — check RoleBinding |
| 404 | Resource does not exist |
| 409 | Conflict on update |

---

## 8. Watch API (streaming changes)

```python
from kubernetes import watch

w = watch.Watch()
for event in w.stream(v1.list_namespaced_pod, namespace="handbook-lab", timeout_seconds=60):
    print(event["type"], event["object"].metadata.name)
```

Use watches for long-lived controllers; use list+polling for short CI scripts.

---

## 9. Lab — Day 17

Work from `python/day17/labs/`. Requires a cluster and `kubectl` access (Kubernetes handbook Day 1+).

1. `pip install kubernetes`.
2. Run `python k8s_status.py pods` — all pods in `default` or `--namespace handbook-lab`.
3. Run `python k8s_status.py deployments --all-namespaces`.
4. Deploy sample nginx to `handbook-lab`; run `python k8s_status.py wait-deploy web handbook-lab`.
5. Run with invalid namespace — confirm ApiException is handled cleanly.
6. Compare output with `kubectl get pods -n handbook-lab -o wide`.

**Stretch:** Export deployment summary JSON for a Slack webhook notifier.

---

## 10. DevOps connections

- **GitOps (Argo CD/Flux):** Apply stays in Git; Python validates live state vs expectations.
- **CI gates:** Block promote if `ready_replicas < spec.replicas`.
- **Custom operators:** Production controllers extend the same client with reconcile loops.

---

## Quick reference

| Task | client-python |
|------|---------------|
| Load config | `config.load_kube_config()` |
| List pods | `CoreV1Api().list_namespaced_pod(ns)` |
| List deployments | `AppsV1Api().list_namespaced_deployment(ns)` |
| Read one deploy | `read_namespaced_deployment(name, ns)` |
| Label filter | `label_selector="app=web"` |

**Next:** [Day 18 — SSH automation with Paramiko](../day18/)
