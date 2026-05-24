# Day 27 — Troubleshooting Methodology

**Goal:** Systematically diagnose cluster and workload failures using a repeatable framework, essential commands, and common failure scenarios.

**Time:** 5–6 hours

---

## 1. The DEBUG framework

| Step | Action |
|------|--------|
| **D**escribe | `kubectl describe` — events tell the story |
| **E**vents | `kubectl get events --sort-by=...` |
| **B**ottom-up | Node → kubelet → Pod → container → app |
| **U**nderstand changes | What deployed/changed recently? |
| **G**ather logs | Pod logs, previous, sidecars, node logs |

Always ask: **Is it the cluster, the platform, or the app?**

---

## 2. First 60 seconds checklist

```bash
kubectl get nodes
kubectl get pods -A | grep -v Running
kubectl get events -A --sort-by='.lastTimestamp' | tail -30
kubectl top nodes 2>/dev/null
kubectl -n kube-system get pods
```

---

## 3. Pod failure playbook

| Status | Commands | Common fixes |
|--------|----------|--------------|
| **Pending** | `describe pod`, `describe node` | Resources, taints, PVC, affinity |
| **ImagePullBackOff** | `describe pod` | Tag, registry auth, network |
| **CrashLoopBackOff** | `logs --previous` | App error, wrong cmd, missing config |
| **OOMKilled** | `describe`, metrics | Raise memory limit or fix leak |
| **CreateContainerConfigError** | `describe` | Missing CM/Secret key |
| **Running but no traffic** | endpoints, readiness | Fix probe, Service selector |

```bash
kubectl describe pod POD -n NS
kubectl logs POD -n NS --previous
kubectl get endpoints SVC -n NS
kubectl exec -it POD -n NS -- sh
```

---

## 4. Node issues

```bash
kubectl describe node NODE
kubectl get node NODE -o yaml | grep -A5 conditions
kubectl debug node/NODE -it --image=busybox   # K8s 1.23+
```

| Condition | Meaning |
|-----------|---------|
| Ready=False | Node unhealthy |
| MemoryPressure | Evictions imminent |
| DiskPressure | Clean images/logs |
| PIDPressure | Too many processes |

---

## 5. Networking debug

```bash
kubectl run netshoot --rm -it --restart=Never --image=nicolaka/netshoot -n handbook-lab -- bash

# Inside netshoot:
nslookup kubernetes.default
curl -v http://web.handbook-lab.svc.cluster.local
traceroute 10.96.0.1
```

Check: Service selector, NetworkPolicy, Ingress backend, DNS CoreDNS pods.

---

## 6. Control plane (managed vs self-managed)

```bash
kubectl get --raw /readyz?verbose
kubectl get componentstatuses 2>/dev/null
kubectl logs -n kube-system -l component=kube-apiserver --tail=50
```

Managed: use cloud console for API/etcd health.

---

## 7. Useful tools

| Tool | Use |
|------|-----|
| **k9s** | Interactive exploration |
| **stern** | Multi-pod log tail |
| **kubectl-tree** | Ownership hierarchy |
| **kube-capacity** | Resource allocation view |

```bash
kubectl api-resources
kubectl get all -n handbook-lab
kubectl get deploy,rs,pod -n handbook-lab -l app=web
```

---

## 8. Lab — Day 27

Break and fix five scenarios (solo or with checklist):

1. Wrong image tag → ImagePullBackOff
2. Missing ConfigMap key → CreateContainerConfigError
3. Service selector mismatch → curl fails
4. Readiness probe wrong path → 503 via Ingress
5. CPU request too high → Pending

For each: document exact commands used and resolution time.

**Stretch:** Simulate etcd full or disk pressure on node (read-only) — recovery steps on paper.

---

## 9. DevOps connections

- **Incident response:** Severity, comms, rollback via GitOps revert.
- **Postmortems:** Blameless; add probe/alert/runbook.
- **CKA/CKS:** Speed drills on `kubectl` troubleshooting (Day 29).

---

## Quick reference

| Symptom | First command |
|---------|---------------|
| Pod not starting | `kubectl describe pod` |
| App error | `kubectl logs --previous` |
| No traffic | `kubectl get endpoints` |
| Cluster sick | `kubectl get nodes` + kube-system pods |
| Recent changes | `kubectl rollout history` |

**Next:** [Day 28 — Multi-tenancy](../day28/)
