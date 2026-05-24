# Day 18 — Helm: Charts, Values & Releases

**Goal:** Package Kubernetes apps with Helm, install/upgrade/rollback releases, and author a simple chart.

**Time:** 5–6 hours

---

## 1. Why Helm?

| Raw YAML | Helm chart |
|----------|------------|
| Copy-paste per env | Parameterized values |
| No version history | Release revisions |
| Manual ordering | Hooks, dependencies |

Helm 3 is client-only (no Tiller) — `helm` talks to Kubernetes API directly.

---

## 2. Install Helm

```bash
brew install helm
helm version
```

---

## 3. Install a chart

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm search repo nginx

helm install my-nginx bitnami/nginx \
  --namespace handbook-lab \
  --create-namespace \
  --set service.type=ClusterIP \
  --set replicaCount=2

helm list -n handbook-lab
kubectl get all -n handbook-lab -l app.kubernetes.io/instance=my-nginx
```

---

## 4. Upgrade and rollback

```bash
helm upgrade my-nginx bitnami/nginx \
  --namespace handbook-lab \
  --set replicaCount=3 \
  --reuse-values

helm history my-nginx -n handbook-lab
helm rollback my-nginx 1 -n handbook-lab
helm uninstall my-nginx -n handbook-lab
```

---

## 5. Values files

```yaml
# values-staging.yaml
replicaCount: 2
image:
  tag: "1.27"
service:
  type: ClusterIP
resources:
  requests:
    cpu: 100m
    memory: 128Mi
```

```bash
helm install web ./my-chart -f values-staging.yaml -n handbook-lab
helm upgrade web ./my-chart -f values-prod.yaml -n handbook-lab
```

---

## 6. Create a chart

```bash
helm create handbook-web
tree handbook-web
```

Key files:

```
handbook-web/
  Chart.yaml          # metadata, version
  values.yaml         # defaults
  templates/          # Go templates → manifests
    deployment.yaml
    service.yaml
    _helpers.tpl
  charts/             # subchart dependencies
```

Example template snippet:

```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "handbook-web.fullname" . }}
spec:
  replicas: {{ .Values.replicaCount }}
  ...
```

```bash
helm template handbook-web ./handbook-web -f values.yaml   # render locally
helm lint ./handbook-web
helm install handbook-web ./handbook-web -n handbook-lab
```

---

## 7. Hooks and dependencies

```yaml
# annotations on Job for pre-install
"helm.sh/hook": pre-install,pre-upgrade
"helm.sh/hook-weight": "-5"
```

```yaml
# Chart.yaml dependencies
dependencies:
  - name: postgresql
    version: "12.x.x"
    repository: https://charts.bitnami.com/bitnami
```

```bash
helm dependency update ./handbook-web
```

---

## 8. Lab — Day 18

1. Install `bitnami/nginx` as release `lab-nginx` with custom replica count.
2. Upgrade with new values file; verify rollout.
3. Rollback one revision; confirm replica count reverts.
4. `helm create handbook-web`; customize image to `hashicorp/http-echo`; install.
5. Run `helm template` and diff output against `kubectl apply --dry-run=server`.

**Stretch:** Package Day 30 capstone app as Helm chart.

---

## 9. DevOps connections

- **GitOps:** Argo CD syncs Helm charts from Git (Day 23).
- **OCI registries:** `helm push` charts to ECR/GCR/ACR.
- **Alternatives:** Kustomize overlays — many teams use both (Helm + Kustomize post-render).

---

## Quick reference

| Task | Command |
|------|---------|
| Install | `helm install RELEASE CHART -n NS` |
| Upgrade | `helm upgrade RELEASE CHART` |
| History | `helm history RELEASE -n NS` |
| Render | `helm template RELEASE ./chart` |
| Uninstall | `helm uninstall RELEASE -n NS` |

**Next:** [Day 19 — Health probes](../day19/)
