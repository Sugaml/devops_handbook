# Day 29 — Production Checklist & Certification Prep

**Goal:** Validate production readiness with a comprehensive checklist, practice CKA/CKS-style scenarios, and consolidate 30 days of learning.

**Time:** 6 hours

---

## 1. Production readiness checklist

### Cluster & infrastructure

- [ ] Multi-AZ node pools
- [ ] Control plane HA (managed or stacked etcd)
- [ ] etcd backup / Velero schedule tested restore
- [ ] Cluster upgrade runbook tested
- [ ] Node auto-repair / CA configured

### Workloads

- [ ] Deployments with resource requests/limits
- [ ] Liveness + readiness + startup probes
- [ ] PDB on critical services
- [ ] HPA for stateless tiers
- [ ] Non-root, read-only root FS where possible

### Networking

- [ ] Ingress + TLS (cert-manager)
- [ ] NetworkPolicies default-deny baseline
- [ ] Internal vs external Service types documented

### Security

- [ ] RBAC least privilege; no cluster-admin for apps
- [ ] Pod Security enforce baseline/restricted
- [ ] Secrets not in Git; encryption at rest
- [ ] Image scanning in CI; signed images (goal)
- [ ] Audit logging enabled

### Observability

- [ ] Metrics (Prometheus) + dashboards (Grafana)
- [ ] Log aggregation
- [ ] Alerting on SLOs (latency, errors, saturation)
- [ ] On-call runbooks linked from alerts

### Operations

- [ ] GitOps for manifests
- [ ] Documented rollback procedure
- [ ] DR test within last quarter
- [ ] Capacity planning review quarterly

---

## 2. CKA exam patterns (practice)

Time yourself — 2 hours for these drills:

```bash
# 1. Create deployment, expose service, scale
kubectl create deployment ckdrill --image=nginx:1.27-alpine -n handbook-lab
kubectl expose deployment ckdrill --port=80 -n handbook-lab
kubectl scale deployment ckdrill --replicas=4 -n handbook-lab

# 2. Troubleshoot failing pod (create broken one first)
kubectl run broken --image=nginx:badtag -n handbook-lab

# 3. Static pod / node maintenance
kubectl drain NODE --ignore-daemonsets --delete-emptydir-data
kubectl uncordon NODE

# 4. RBAC: create SA, role, rolebinding
# 5. NetworkPolicy or ingress rule from spec
# 6. PersistentVolume claim + mount
# 7. kubectl logs, exec, debug
```

**Tips:** `kubectl explain`, `--dry-run=client -o yaml`, `alias k=kubectl`, practice imperative + declarative.

---

## 3. CKS security patterns (practice)

```bash
# Secure pod
kubectl run secure --image=nginx -n handbook-lab --dry-run=client -o yaml > pod.yaml
# edit: runAsNonRoot, drop ALL caps, readOnlyRootFilesystem

# NetworkPolicy deny all ingress
# Audit: kubectl auth can-i create pods --as=system:serviceaccount:handbook-lab:default

# AppArmor / seccomp profiles (if enabled on cluster)
# Falco / audit policy awareness
```

---

## 4. kubectl speed cheatsheet

```bash
export do="--dry-run=client -o yaml"
kubectl create deployment web --image=nginx $do | kubectl apply -f -

kubectl set image deployment/web nginx=nginx:1.27-alpine -n handbook-lab
kubectl rollout status deployment/web -n handbook-lab
kubectl get events -n handbook-lab --sort-by='.lastTimestamp'

# Force delete stuck pod
kubectl delete pod POD -n handbook-lab --grace-period=0 --force
```

---

## 5. Architecture review questions

Can you whiteboard answers to:

1. Pod → Deployment → Service → Ingress traffic flow?
2. What happens when you `kubectl apply` a changed Deployment?
3. How does HPA get CPU metrics?
4. Difference between ConfigMap and Secret at rest?
5. Why StatefulSet for databases vs Deployment?
6. GitOps drift detection flow?

---

## 6. Lab — Day 29

1. Run production checklist against your kind cluster; score yourself /50 items.
2. Complete three timed CKA drills under 15 minutes each.
3. Create secure Pod manifest passing restricted Pod Security (where possible on kind).
4. Write answers to six architecture questions in section 5.
5. Identify your three weakest topics; re-read those day folders.

**Stretch:** Register for CKA/CKS mock exam (Killer.sh included with CNCF exam).

---

## 7. DevOps connections

- **Interviews:** System design + live kubectl troubleshooting common.
- **Platform engineering:** Checklist becomes team golden standard.
- **Continuous learning:** K8s release every 4 months — subscribe to CHANGELOG.

---

## Quick reference

| Certification | Focus |
|---------------|-------|
| **CKA** | Cluster admin, troubleshooting, storage, networking |
| **CKAD** | Application developer, deploy, configure, observe |
| **CKS** | Security hardening, supply chain, runtime |

**Next:** [Day 30 — Capstone project](../day30/)
