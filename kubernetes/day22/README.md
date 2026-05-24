# Day 22 — CRDs, Operators & Custom Controllers

**Goal:** Extend Kubernetes with CustomResourceDefinitions, understand the operator pattern, and install a real operator.

**Time:** 5–6 hours

---

## 1. Why extend the API?

Built-in resources cover common cases. Platforms need domain-specific objects:

| CRD example | Purpose |
|-------------|---------|
| `Certificate` (cert-manager) | TLS lifecycle |
| `Prometheus` (Prometheus Operator) | Monitoring stack |
| `PostgresCluster` (Crunchy) | Database ops |

---

## 2. CustomResourceDefinition

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: widgets.handbook.devops
spec:
  group: handbook.devops
  scope: Namespaced
  names:
    plural: widgets
    singular: widget
    kind: Widget
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                size:
                  type: string
                replicas:
                  type: integer
```

```yaml
apiVersion: handbook.devops/v1
kind: Widget
metadata:
  name: demo
  namespace: handbook-lab
spec:
  size: large
  replicas: 3
```

```bash
kubectl apply -f crd.yaml
kubectl apply -f widget.yaml
kubectl get widgets -n handbook-lab
kubectl explain widget.spec
```

---

## 3. Operator pattern

```
User creates Custom Resource (desired state)
        │
        ▼
Operator controller watches CR
        │
        ▼
Reconcile loop creates/updates native K8s objects (Deploy, Svc, PVC...)
        │
        ▼
Updates CR .status
```

Operators encode operational knowledge (backup, failover, upgrades).

---

## 4. Install cert-manager (real operator)

```bash
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set crds.enabled=true

kubectl get crd | grep cert-manager
kubectl get pods -n cert-manager
```

Creates `Certificate`, `ClusterIssuer`, etc. — industry-standard CRDs.

---

## 5. Controller tools

| Tool | Language |
|------|----------|
| Kubebuilder | Go |
| Operator SDK | Go, Ansible, Helm |
| Kopf | Python |
| Java Operator SDK | Java |

---

## 6. Lab — Day 22

1. Apply simple Widget CRD + one Widget instance.
2. `kubectl get crd` and find cert-manager CRDs (install if not present).
3. Create ClusterIssuer (self-signed) and Certificate for `web.localdev.me` — read cert-manager docs.
4. Observe cert-manager controller logs during certificate issuance.
5. Delete Widget CR; CRD remains; understand CR vs CRD lifecycle.

**Stretch:** Scaffold operator with `kubebuilder init` (read generated files only).

---

## 7. DevOps connections

- **Platform teams** ship operators as internal products.
- **Version skew:** Upgrade operators before CRD schema changes.
- **GitOps:** Custom resources synced like Deployments (Day 23).

---

## Quick reference

| Task | Command |
|------|---------|
| List CRDs | `kubectl get crd` |
| Custom resources | `kubectl get <plural> -n NS` |
| Explain CR | `kubectl explain KIND.spec` |
| Operator logs | `kubectl logs -n operator-ns deploy/...` |

**Next:** [Day 23 — GitOps](../day23/)
