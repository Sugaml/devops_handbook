# Day 26 — Security: Admission, Pod Security & Supply Chain

**Goal:** Harden clusters with Pod Security standards, admission controllers, OPA/Gatekeeper policies, and secure image supply chain practices.

**Time:** 6 hours

---

## 1. Defense in depth layers

```
Cloud IAM → RBAC → NetworkPolicy → Pod Security → Admission policies → App security
```

No single layer is sufficient.

---

## 2. Pod Security Standards (built-in)

Replaces PodSecurityPolicy (removed 1.25).

| Level | Description |
|-------|-------------|
| **Privileged** | Unrestricted |
| **Baseline** | Minimally restrictive, blocks known escalations |
| **Restricted** | Hardened pod spec |

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: handbook-lab
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

Violations blocked at admission when `enforce` is set.

---

## 3. Secure pod spec checklist

```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: app
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: ["ALL"]
```

---

## 4. OPA Gatekeeper (policy as code)

```bash
helm install gatekeeper gatekeeper/gatekeeper \
  --namespace gatekeeper-system --create-namespace
```

Example ConstraintTemplate — require labels:

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: require-app-label
spec:
  match:
    kinds:
      - apiGroups: ["apps"]
        kinds: ["Deployment"]
  parameters:
    labels: ["app.kubernetes.io/name"]
```

---

## 5. Image supply chain

| Practice | Tool |
|----------|------|
| Scan images | Trivy, Grype, Snyk |
| Sign images | Cosign, Notary |
| Verify at admission | Kyverno verifyImages, Gatekeeper |
| Minimal base | distroless, alpine, chainguard |

```bash
trivy image nginx:1.27-alpine
cosign sign --key cosign.key myregistry.io/app:v1.0
```

---

## 6. Secrets and etcd

- Enable encryption at rest for Secrets
- Restrict `get secrets` RBAC
- Use external secret managers (Day 9)
- Rotate ServiceAccount tokens (short-lived projected tokens)

---

## 7. API server hardening

- Disable anonymous auth
- Audit logging enabled
- Restrict `--insecure-port` (removed in modern versions)
- Private endpoint for managed clusters

```bash
kubectl get --raw /healthz
kubectl auth can-i '*' '*' --all-namespaces   # should be no for dev SA
```

---

## 8. Lab — Day 26

1. Label namespace with Pod Security `enforce: baseline`.
2. Try deploying privileged Pod (`privileged: true`); confirm rejection.
3. Fix Deployment with `runAsNonRoot`, dropped capabilities; deploy successfully.
4. Scan three images with Trivy; document CVE severity counts.
5. Write RBAC rule denying `secrets` list for developer Role.

**Stretch:** Install Gatekeeper and apply one Constraint from official library.

---

## 9. DevOps connections

- **Compliance:** CIS Kubernetes Benchmark, NSA hardening guide.
- **CI:** Block deploy on critical CVEs; sign images in pipeline.
- **Zero trust:** mTLS mesh + NP + restricted PSS together.

---

## Quick reference

| Task | Command |
|------|---------|
| PSS labels | namespace `pod-security.kubernetes.io/enforce` |
| Scan image | `trivy image IMAGE` |
| Audit RBAC | `kubectl auth can-i --list` |
| Secure context | `securityContext` pod + container |

**Next:** [Day 27 — Troubleshooting](../day27/)
