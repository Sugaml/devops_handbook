# Day 13 — RBAC: Roles, Bindings & Least Privilege

**Goal:** Control who can do what in the cluster using Roles, ClusterRoles, RoleBindings, and ClusterRoleBindings.

**Time:** 5–6 hours

---

## 1. RBAC model

```
Subject (User | Group | ServiceAccount)
    │
    ▼
RoleBinding / ClusterRoleBinding
    │
    ▼
Role / ClusterRole  (rules: verbs + resources)
```

| Scope | Role type | Binding type |
|-------|-----------|--------------|
| Namespace | Role | RoleBinding |
| Cluster-wide | ClusterRole | ClusterRoleBinding or RoleBinding |

---

## 2. Role example — read pods in one namespace

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: handbook-lab
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: handbook-lab
subjects:
  - kind: User
    name: dev-alice
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

---

## 3. ClusterRole — cluster-scoped resources

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-viewer
rules:
  - apiGroups: [""]
    resources: ["nodes"]
    verbs: ["get", "list", "watch"]
```

Common built-in ClusterRoles: `view`, `edit`, `admin`, `cluster-admin`.

```bash
kubectl get clusterrole
kubectl describe clusterrole view
```

---

## 4. Verbs and resources

| Verb | Meaning |
|------|---------|
| get, list, watch | Read |
| create, update, patch | Write |
| delete | Delete |
| * | All verbs |

```bash
# What can I do?
kubectl auth can-i create deployments -n handbook-lab
kubectl auth can-i delete nodes
kubectl auth can-i --list -n handbook-lab

# As another user/SA
kubectl auth can-i get secrets --as=system:serviceaccount:handbook-lab:default -n handbook-lab
```

---

## 5. Aggregated ClusterRoles

Built-in roles like `admin` aggregate rules from labeled ClusterRoles — extend platform permissions carefully.

---

## 6. Principle of least privilege

| Role pattern | Typical grant |
|--------------|---------------|
| Developer | `edit` in dev namespace only |
| CI deploy SA | create/update deployments, services — no secrets read |
| Read-only SRE | `view` + custom metrics |
| Break-glass | cluster-admin — audited, time-limited |

**Never** give cluster-admin to application ServiceAccounts.

---

## 7. Lab — Day 13

1. Create Role `pod-reader` and RoleBinding for a test ServiceAccount (Day 14).
2. Verify SA can `get pods` but cannot `delete pods`.
3. Use `kubectl auth can-i` to prove permissions before/after binding.
4. Create ClusterRole `ns-lister` (list namespaces); bind to SA; verify cross-namespace list works but get secrets fails.
5. Review built-in `view` vs `edit` diff with `kubectl describe clusterrole`.

**Stretch:** Use [rbac-manager](https://fairwinds.com/rbac-manager) or OPA (Day 26) docs as reading.

---

## 8. DevOps connections

- **Cloud IAM:** EKS/GKE map IAM users/groups to K8s RBAC via `aws-auth` / GKE RBAC.
- **Audit:** Log denied API calls — common security finding.
- **GitOps:** Deploy RBAC manifests from repo like app code.

---

## Quick reference

| Task | Command |
|------|---------|
| Can I? | `kubectl auth can-i VERB RESOURCE -n NS` |
| List roles | `kubectl get role,rolebinding -n NS` |
| Describe rules | `kubectl describe role NAME -n NS` |

**Next:** [Day 14 — Service accounts](../day14/)
