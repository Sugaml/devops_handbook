# Day 9 — Secrets & Sensitive Data

**Goal:** Store and mount credentials safely, understand base64 encoding vs encryption, integrate with external secret stores, and avoid common leaks.

**Time:** 4–5 hours

---

## 1. Kubernetes Secret types

| type | Use |
|------|-----|
| `Opaque` | Generic key-value (default) |
| `kubernetes.io/tls` | TLS cert + key |
| `kubernetes.io/dockerconfigjson` | Registry pull credentials |
| `kubernetes.io/basic-auth` | Basic auth username/password |

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
  namespace: handbook-lab
type: Opaque
stringData:          # plain text — encoded on apply
  username: appuser
  password: changeme-in-lab-only
# data:              # base64 encoded values
#   username: YXBwdXNlcg==
```

```bash
kubectl apply -f secret.yaml
kubectl get secret db-credentials -n handbook-lab
kubectl describe secret db-credentials -n handbook-lab   # values hidden
```

---

## 2. Create secrets imperatively

```bash
kubectl create secret generic db-credentials \
  --from-literal=username=appuser \
  --from-literal=password='s3cret!' \
  -n handbook-lab

kubectl create secret tls web-tls --cert=tls.crt --key=tls.key -n handbook-lab

kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=pass \
  -n handbook-lab
```

---

## 3. Use in Pods

```yaml
spec:
  imagePullSecrets:
    - name: regcred
  containers:
    - name: app
      env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
      volumeMounts:
        - name: secrets
          mountPath: /etc/secrets
          readOnly: true
  volumes:
    - name: secrets
      secret:
        secretName: db-credentials
```

Fix typo in volumes - should be `name` not `names`. Let me fix when writing... Actually I wrote `names` by mistake. I'll fix in the file.

---

## 4. Encryption at rest

By default etcd stores Secrets base64-encoded, **not encrypted**.

Enable **encryption at rest** via `EncryptionConfiguration` on API server (managed clouds often provide KMS integration).

**Never commit Secrets to Git** — use Sealed Secrets, SOPS, External Secrets Operator, or cloud secret managers.

---

## 5. External Secrets pattern

```
AWS Secrets Manager / Vault / GCP SM
         │
         ▼
External Secrets Operator → Kubernetes Secret → Pod
```

Production teams sync secrets via CI or operators; developers reference Secret names only.

---

## 6. Security hygiene

| Do | Don't |
|----|-------|
| RBAC limit who reads Secrets | Log secret values |
| Rotate credentials | Put secrets in ConfigMaps |
| Use `stringData` in local dev only | Commit unencrypted YAML to Git |
| Audit `kubectl get secret -o yaml` access | Share cluster-admin kubeconfig |

```bash
# Decode (lab only — proves encoding ≠ encryption)
kubectl get secret db-credentials -n handbook-lab -o jsonpath='{.data.password}' | base64 -d; echo
```

---

## 7. Lab — Day 9

1. Create Secret `db-credentials` with username/password.
2. Deploy Pod that prints `DB_PASSWORD` from env (busybox + secretKeyRef).
3. Mount same Secret as files under `/etc/secrets/`; `cat` files inside Pod.
4. Create TLS secret; attach to Ingress from Day 7.
5. Write `.gitignore` rule for `*secret*.yaml` in your lab repo.

**Stretch:** Read about [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) — encrypt for Git storage.

---

## 8. DevOps connections

- **CI/CD:** Pipeline creates short-lived Secrets or uses IRSA/Workload Identity instead of long-lived keys.
- **Compliance:** Secret rotation + audit logs are common audit findings.
- **Service mesh:** mTLS reduces some secret sprawl for service-to-service auth.

---

## Quick reference

| Task | Command |
|------|---------|
| Create generic | `kubectl create secret generic NAME --from-literal=k=v` |
| TLS secret | `kubectl create secret tls NAME --cert= --key=` |
| Decode value | `-o jsonpath='{.data.key}' \| base64 -d` |
| Docker pull secret | `--type=kubernetes.io/dockerconfigjson` |

**Next:** [Day 10 — Resources & QoS](../day10/)
