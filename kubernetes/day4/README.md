# Day 4 — Labels, Selectors & Annotations

**Goal:** Use labels for identification and selection, understand how controllers and Services match Pods, and apply annotations for metadata.

**Time:** 3–4 hours

---

## 1. Labels vs annotations

| | Labels | Annotations |
|---|--------|-------------|
| **Purpose** | Identify & select objects | Non-identifying metadata |
| **Used in selectors** | Yes | No |
| **Example keys** | `app`, `env`, `tier` | `description`, `git-sha`, `owner` |
| **Size limit** | 63 char keys/values | Large values OK |

```yaml
metadata:
  labels:
    app: web
    env: staging
    tier: frontend
  annotations:
    kubernetes.io/change-cause: "deploy v1.2.3"
    contact: "team-platform@example.com"
```

---

## 2. Label selectors

### Equality-based

```bash
kubectl get pods -l app=web
kubectl get pods -l 'env in (staging,dev)'
kubectl get pods -l 'tier notin (backend)'
kubectl get pods -l app=web,env=staging   # AND
```

### Set-based in manifests

```yaml
spec:
  selector:
    matchLabels:
      app: web
    matchExpressions:
      - key: env
        operator: In
        values: [staging, prod]
      - key: tier
        operator: NotIn
        values: [batch]
```

---

## 3. How selectors wire the system

```
Deployment.spec.selector  ──matches──▶  Pod labels
       │
       └── creates/manages ReplicaSet

Service.spec.selector     ──matches──▶  Pod labels
       │
       └── Endpoints / EndpointSlice

NetworkPolicy.spec.podSelector ──matches──▶ Pod labels
```

**Immutable rule:** Deployment `spec.selector` cannot change after creation — plan labels early.

---

## 4. Recommended label conventions

Kubernetes recommended labels ([docs](https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/)):

```yaml
labels:
  app.kubernetes.io/name: web
  app.kubernetes.io/instance: web-staging
  app.kubernetes.io/version: "1.2.0"
  app.kubernetes.io/component: frontend
  app.kubernetes.io/part-of: shop
  app.kubernetes.io/managed-by: helm
```

Use consistent keys across Deployments, Services, NetworkPolicies, and monitoring.

---

## 5. Imperative label management

```bash
kubectl label pod api-v1 tier=frontend -n handbook-lab
kubectl label pod api-v1 env-  # remove label
kubectl annotate pod api-v1 deploy-date="2026-05-24" -n handbook-lab

# Show labels in columns
kubectl get pods -n handbook-lab -L app,tier,env
```

---

## 6. Field selectors (different from labels)

```bash
kubectl get pods --field-selector status.phase=Running -n handbook-lab
kubectl get pods --field-selector spec.nodeName=kind-devops-handbook-worker
```

Fields are built-in object fields, not user-defined labels.

---

## 7. Lab — Day 4

1. Create three Pods with labels `app=web`, `env=dev|staging|prod` (use one manifest with different metadata or three files).
2. List only `env=staging` pods.
3. Create a Deployment `web` with selector `app=web, tier=frontend`; verify ReplicaSet inherits labels.
4. Add annotation `git-sha: abc123` to the Deployment; confirm annotations are not in `kubectl get pods -l`.
5. Use `kubectl get pods --show-labels` and `-L env` to compare output.

**Stretch:** Query API directly: `kubectl get pods -n handbook-lab -l env=prod -o json | jq '.items[].metadata.labels'`.

---

## 8. DevOps connections

- **Prometheus/Grafana:** ServiceMonitor selects targets by labels.
- **GitOps:** Labels drive which apps sync to which clusters.
- **Cost allocation:** Labels like `team`, `cost-center` feed billing exports on cloud.

---

## Quick reference

| Task | Command |
|------|---------|
| Filter by label | `kubectl get pods -l key=value` |
| Add label | `kubectl label pod NAME key=value` |
| Show labels | `--show-labels` or `-L key` |
| Set in YAML | `metadata.labels` |

**Next:** [Day 5 — Deployments](../day5/)
