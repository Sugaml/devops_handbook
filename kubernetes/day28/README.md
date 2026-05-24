# Day 28 — Multi-Tenancy, Namespaces & Platform Scale

**Goal:** Design namespace strategy, enforce tenant isolation with RBAC/quotas/policies, and operate shared clusters at platform scale.

**Time:** 5 hours

---

## 1. Tenancy models

| Model | Isolation | Cost | Use case |
|-------|-----------|------|----------|
| **Soft multi-tenant** | Namespace + RBAC + quotas | Low | Internal teams |
| **Hard multi-tenant** | Virtual clusters (vcluster), separate clusters | Medium | Untrusted tenants |
| **Cluster per tenant** | Full isolation | High | Regulated workloads |

Most enterprises: shared cluster with strong namespace boundaries.

---

## 2. Namespace strategy

```
team-platform     # shared infra operators
team-payments-dev
team-payments-prod
team-analytics-dev
```

Labels for cost and policy:

```yaml
metadata:
  labels:
    team: payments
    env: prod
    cost-center: CC-1234
  annotations:
    owner: platform@example.com
```

Avoid "namespace per microservice" — operational overhead explodes.

---

## 3. Resource isolation stack

Per namespace:

```yaml
# ResourceQuota — cap total resources
# LimitRange — defaults and max per container
# NetworkPolicy — default deny + allowlists
# Pod Security — enforce baseline/restricted
# RBAC RoleBindings — team access only their NS
```

```bash
kubectl create quota team-quota \
  --hard=cpu=8,memory=16Gi,pods=50 \
  -n team-payments-dev
```

---

## 4. Hierarchical namespaces (HNC)

[Hierarchy Controller](https://github.com/kubernetes-sigs/hierarchical-namespaces) — parent namespace propagates policies to children.

Useful for: `payments` parent → `payments-dev`, `payments-staging`, `payments-prod` inheriting common RBAC.

---

## 5. Fair scheduling and noisy neighbors

- ResourceQuota + LimitRange
- PriorityClasses for critical system vs batch workloads
- Separate node pools / taints for GPU, batch, system

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000
globalDefault: false
```

---

## 6. Platform team responsibilities

| Area | Deliverable |
|------|-------------|
| Cluster lifecycle | Upgrades, node pools |
| Add-ons | Ingress, cert-manager, monitoring |
| Self-service | Namespace provisioning API/ ticket |
| Guardrails | PSS, Gatekeeper, quotas |
| Documentation | Golden paths, runbooks |

---

## 7. Lab — Day 28

1. Create namespaces `team-a-dev` and `team-b-dev` with team labels.
2. Create Role `team-admin` (full access in one NS only); bind to SA per team.
3. Apply ResourceQuota cpu=2, memory=4Gi to each; exceed quota and observe denial.
4. Apply default-deny NetworkPolicy in `team-a-dev`; allow DNS egress only.
5. Verify team-a SA cannot list pods in team-b namespace.

**Stretch:** Design namespace naming convention doc for fictional 50-team org.

---

## 8. DevOps connections

- **Chargeback/showback:** Labels → cost reports (Kubecost, cloud billing).
- **Self-service portals:** Backstage, custom operators create namespaces from template.
- **Compliance:** Prod namespaces get restricted PSS; dev gets baseline.

---

## Quick reference

| Task | Command |
|------|---------|
| NS labels | `kubectl label ns NAME team=...` |
| Quota usage | `kubectl describe quota -n NS` |
| Cross-NS access | test with `kubectl auth can-i --as=...` |
| Priority | `priorityClassName` in pod spec |

**Next:** [Day 29 — Production checklist & cert prep](../day29/)
