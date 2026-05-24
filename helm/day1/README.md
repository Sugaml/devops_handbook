# Day 1 — Helm Concepts, Install & Your First Release

**Goal:** Understand why Helm exists, install Helm 3, add a chart repository, and manage a full release lifecycle (install → upgrade → rollback → uninstall).

**Time:** 3–5 hours (theory + hands-on)

---

## 1. Why Helm?

| Without Helm | With Helm |
|--------------|-----------|
| Copy-paste YAML across environments | One chart + environment-specific `values.yaml` |
| Manual ordering (CRD → operator → app) | Dependencies and hooks |
| “Which manifest set is prod?” | **Release** = versioned deployment of a chart |
| Undocumented image tags in YAML | Defaults in `values.yaml`, overrides in CI |

Helm is the **package manager** for Kubernetes: charts are packages, releases are installed instances.

**Helm 3 changes that matter:**

- **No Tiller** — `helm` talks to Kubernetes API directly (RBAC is yours to configure).
- **Release storage** — release metadata stored in Secrets (default) in the release namespace.
- **Three-way merge** on upgrade — live state, last applied manifest, new manifest.

---

## 2. Core vocabulary

| Term | Meaning |
|------|---------|
| **Chart** | Directory of templates + default values + metadata (`Chart.yaml`) |
| **Release** | A chart instance running in a cluster (name + revision history) |
| **Repository** | HTTP or OCI index of packaged charts |
| **Values** | Inputs that template into manifests |
| **Revision** | Numbered install/upgrade (used for rollback) |

```
  Chart (package)  +  Values  --helm install-->  Release (revision 1, 2, …)
        │                                              │
        └── templates/*.yaml                           └── live K8s objects
```

---

## 3. Install Helm 3

```bash
# macOS
brew install helm

# Linux (script)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

helm version
# version.BuildInfo{Version:"v3.x.x", ...}
```

Verify cluster access (Helm uses your kubeconfig):

```bash
kubectl cluster-info
kubectl get nodes
kubectl create namespace helm-handbook --dry-run=client -o yaml | kubectl apply -f -
```

---

## 4. Repositories and search

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm search repo nginx
helm search repo bitnami/nginx --versions | head -5

# Inspect a chart without installing
helm show chart bitnami/nginx
helm show values bitnami/nginx | head -40
helm show readme bitnami/nginx
```

**Production note:** Pin chart **version** in CI (`helm install … --version 15.3.4`), not “latest”.

---

## 5. First install

Install NGINX from Bitnami with a custom release name:

```bash
helm install my-nginx bitnami/nginx \
  --namespace helm-handbook \
  --set service.type=ClusterIP \
  --set replicaCount=1

helm list -n helm-handbook
kubectl get pods,svc -n helm-handbook -l app.kubernetes.io/instance=my-nginx
```

What Helm created:

```bash
helm get manifest my-nginx -n helm-handbook | head -50
helm get values my-nginx -n helm-handbook
helm get notes my-nginx -n helm-handbook
helm status my-nginx -n helm-handbook
```

---

## 6. Upgrade and rollback

```bash
# Change a value
helm upgrade my-nginx bitnami/nginx \
  -n helm-handbook \
  --reuse-values \
  --set replicaCount=2

helm history my-nginx -n helm-handbook

# Roll back to revision 1
helm rollback my-nginx 1 -n helm-handbook

kubectl get deploy -n helm-handbook -o wide
```

| Flag | When to use |
|------|-------------|
| `--reuse-values` | Keep prior user values; only change what you `--set` |
| `-f prod.yaml` | Environment file overrides (preferred in prod) |
| `--reset-values` | Ignore prior release values; use chart defaults + your flags |

---

## 7. Uninstall and cleanup

```bash
helm uninstall my-nginx -n helm-handbook

# Confirm resources gone (some charts leave PVCs by design)
kubectl get all -n helm-handbook
```

---

## 8. Dry-run and debugging (preview only)

```bash
helm install preview bitnami/nginx \
  -n helm-handbook \
  --dry-run \
  --debug \
  --set replicaCount=3 2>&1 | less
```

- `--dry-run` — render and validate without persisting release.
- `--debug` — print generated manifests to stderr.

Day 2 covers `helm template` for offline rendering without cluster calls.

---

## 9. Namespaces and release scope

```bash
# Install into namespace (creates namespace if chart has hook/template — not all do)
helm install api bitnami/nginx -n helm-handbook --create-namespace

# List all namespaces
helm list -A
```

Helm 3 stores release metadata **in the namespace of the release** (unless you configure cluster-wide storage).

---

## 10. Lab — Day 1

1. Add `bitnami` and `ingress-nginx` repos; run `helm repo update`.
2. `helm show values bitnami/nginx` — find `replicaCount` and `service.type`; write them down.
3. Install release `lab-nginx` in `helm-handbook` with `replicaCount=2` and `ClusterIP`.
4. Run `helm history lab-nginx` after an upgrade that sets `replicaCount=1`.
5. Roll back to revision 1; verify pod count with `kubectl get pods -n helm-handbook`.
6. `helm uninstall lab-nginx`; confirm no Deployments remain for that release.

**Stretch:** Install `ingress-nginx/ingress-nginx` with `--set controller.service.type=NodePort` (or ClusterIP on kind) and read `helm get notes`.

---

## 11. DevOps connections

- **Immutable releases:** Each `helm upgrade` bumps revision — treat history like deploy audit trail.
- **Git vs cluster:** Helm values in Git should match what CI applies; drift detection is Day 7 (GitOps).
- **Platform teams:** Curated internal chart repos are how orgs standardize labels, probes, and security contexts.

---

## Quick reference

| Task | Command |
|------|---------|
| Add repo | `helm repo add NAME URL` |
| Search | `helm search repo KEYWORD` |
| Install | `helm install RELEASE CHART -n NS` |
| Upgrade | `helm upgrade RELEASE CHART -n NS` |
| History | `helm history RELEASE -n NS` |
| Rollback | `helm rollback RELEASE REV -n NS` |
| Uninstall | `helm uninstall RELEASE -n NS` |
| List | `helm list -n NS` |

**Next:** [Day 2 — Chart anatomy & your first custom chart](../day2/)
