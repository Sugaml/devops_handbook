# Day 14 — Service Accounts & In-Cluster API Access

**Goal:** Use ServiceAccounts for Pod identity, mount tokens safely, and integrate with cloud IAM (IRSA / Workload Identity).

**Time:** 4–5 hours

---

## 1. Default ServiceAccount

Every namespace has `default` ServiceAccount; Pods use it unless specified.

```bash
kubectl get sa -n handbook-lab
kubectl describe sa default -n handbook-lab
```

---

## 2. Custom ServiceAccount

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
  namespace: handbook-lab
---
apiVersion: v1
kind: Pod
metadata:
  name: api
  namespace: handbook-lab
spec:
  serviceAccountName: app-sa
  containers:
    - name: app
      image: bitnami/kubectl:1.30
      command: ["sleep", "3600"]
```

---

## 3. Token projection (modern default)

Legacy: Secret-based long-lived tokens. **BoundServiceAccountToken** (projected volume) — short-lived, audience-bound.

```yaml
spec:
  containers:
    - name: app
      volumeMounts:
        - name: token
          mountPath: /var/run/secrets/tokens
  volumes:
    - name: token
      projected:
        sources:
          - serviceAccountToken:
              path: token
              expirationSeconds: 3600
              audience: api
```

Inside Pod:

```bash
TOKEN=$(cat /var/run/secrets/tokens/token)
curl -k -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/api/v1/namespaces/handbook-lab/pods
```

---

## 4. ImagePullSecrets on ServiceAccount

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
  namespace: handbook-lab
imagePullSecrets:
  - name: regcred
```

Cleaner than per-Pod `imagePullSecrets`.

---

## 5. Cloud workload identity

| Cloud | Pattern |
|-------|---------|
| **AWS EKS** | IRSA — annotate SA with IAM role ARN |
| **GKE** | Workload Identity — `iam.gke.io/gcp-service-account` |
| **Azure AKS** | Azure AD Workload Identity |

Example EKS annotation:

```yaml
metadata:
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/my-app-role
```

Pod code uses AWS SDK — no static keys in cluster.

---

## 6. Lab — Day 14

1. Create ServiceAccount `pod-reader-sa`.
2. Bind Day 13 `pod-reader` Role to this SA.
3. Run Pod using `bitnami/kubectl` as `pod-reader-sa`; list pods successfully; confirm delete denied.
4. Inspect mounted token path at `/var/run/secrets/kubernetes.io/serviceaccount/`.
5. Document why app Pods should not use cluster-admin SA.

**Stretch:** Read your cloud provider's workload identity setup guide (even if using kind locally).

---

## 7. DevOps connections

- **CI/CD deploy SA:** Dedicated SA per pipeline with minimal RBAC.
- **Multi-tenancy:** One SA per app per namespace.
- **Token theft:** Compromised Pod + powerful SA = cluster compromise — least privilege critical.

---

## Quick reference

| Task | Command |
|------|---------|
| List SA | `kubectl get sa -n NS` |
| Pod SA | `spec.serviceAccountName` |
| Test API | curl with Bearer token inside Pod |
| Can-i as SA | `kubectl auth can-i ... --as=system:serviceaccount:NS:NAME` |

**Next:** [Day 15 — NetworkPolicies](../day15/)
