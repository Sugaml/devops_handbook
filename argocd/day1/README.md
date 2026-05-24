# Day 1 — GitOps, Argo CD Architecture & Install

**Goal:** Understand GitOps principles, how Argo CD reconciles cluster state from Git, install Argo CD on a lab cluster, and authenticate with the CLI and UI.

**Time:** 4–6 hours (theory + hands-on)

---

## 1. Why GitOps?

| Traditional push deploy | GitOps (pull reconcile) |
|-------------------------|-------------------------|
| CI/CD holds cluster credentials | Cluster pulls from Git; CI only updates Git |
| `kubectl apply` from laptops | Declarative desired state in version control |
| "What is running in prod?" is unclear | Git commit = audit trail of intent |
| Rollback = re-run pipeline or manual fix | Rollback = `git revert` + sync (or sync to old commit) |

**GitOps** means the **desired state** of the system lives in Git. A controller (Argo CD) continuously compares live cluster state to Git and applies differences.

Argo CD is **not** a CI tool — it is a **continuous delivery** tool. Build and test in Jenkins, GitHub Actions, or GitLab CI; **promote** by merging to an environment branch or updating a manifest tag.

---

## 2. Argo CD architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         Git / Helm / OCI                         │
│              (GitHub, GitLab, Bitbucket, Chart museum)           │
└─────────────────────────────┬────────────────────────────────────┘
                              │ clone / fetch / helm template
┌─────────────────────────────▼────────────────────────────────────┐
│  ARGO CD (namespace: argocd)                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │ API Server  │  │ Repo Server  │  │ Application Controller  │  │
│  │ (UI + REST) │  │ (manifest    │  │ (reconcile loop)        │  │
│  │             │  │  generation) │  │                         │  │
│  └──────┬──────┘  └──────────────┘  └───────────┬─────────────┘  │
│         │                                        │               │
│  ┌──────▼──────┐  ┌──────────────┐               │               │
│  │ Redis       │  │ Dex (SSO)    │               │               │
│  │ (cache)     │  │ optional     │               │               │
│  └─────────────┘  └──────────────┘               │               │
└──────────────────────────────────────────────────┼───────────────┘
                                                   │ kubectl apply
┌──────────────────────────────────────────────────▼───────────────┐
│  Kubernetes API → Deployments, Services, CRDs, …                 │
└──────────────────────────────────────────────────────────────────┘
```

### Key components

| Component | Role |
|-----------|------|
| **API Server** | gRPC/REST + Web UI; exposes Application CRUD, sync, rollback |
| **Repo Server** | Clones repos, runs `helm template`, `kustomize build`, config management plugins |
| **Application Controller** | Watches `Application` CRs; compares desired vs live; syncs |
| **Redis** | Caches repo metadata and manifest generation |
| **Application** | Custom resource — one deployable unit (usually one app per env) |
| **AppProject** | Logical boundary — allowed repos, clusters, namespaces, RBAC |

**Mental model:** Same as Kubernetes controllers — `spec` (Git pointer) vs `status` (sync/health). You declare **where** Git lives and **where** it should run; Argo CD reconciles.

---

## 3. Core vocabulary

| Term | Meaning |
|------|---------|
| **Application** | CR linking a Git/Helm/OCI source to a cluster namespace |
| **Sync** | Apply generated manifests to the cluster |
| **Refresh** | Re-fetch Git and compare (does not apply by default) |
| **Health** | Aggregate status — Is the app running correctly? |
| **Sync status** | Is live state == desired state? |
| **Destination** | Target cluster URL + namespace |
| **Source** | Repo URL, path, revision (branch/tag/commit), chart name |

```
  Git commit (desired)  ──compare──►  Cluster (live)
         │                                    │
         └────────── Sync applies ────────────┘
```

---

## 4. Prerequisites — lab cluster

If you do not have a cluster from the [Kubernetes handbook](../kubernetes/day1/):

```bash
kind create cluster --name devops-handbook
kubectl cluster-info --context kind-devops-handbook
kubectl get nodes
```

Create a namespace for sample apps (used from Day 2 onward):

```bash
kubectl create namespace handbook-lab
```

---

## 5. Install Argo CD

### Option A — Official manifest (recommended for learning)

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

kubectl wait --for=condition=available --timeout=300s \
  deployment/argocd-server -n argocd

kubectl get pods -n argocd
kubectl get svc -n argocd
```

### Option B — Helm (production-style)

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

helm install argocd argo/argo-cd \
  --namespace argocd \
  --create-namespace \
  --set server.service.type=NodePort \
  --set configs.params."server\.insecure"=true

kubectl get pods -n argocd -w
```

**Production note:** Use Helm with values for HA (`controller.replicas`, `redis-ha`), ingress, TLS, and SSO. Day 7 covers HA patterns.

---

## 6. Access the UI

### Port-forward (simplest for kind/minikube)

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Open **https://localhost:8080** (accept self-signed cert warning).

### Initial admin password

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo
```

Login: username `admin`, password from above.

**Security:** Delete or rotate the initial secret after setting up SSO or a new admin password (Day 5).

---

## 7. Install and configure the CLI

```bash
# macOS
brew install argocd

# Linux
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd-linux-amd64 && sudo mv argocd-linux-amd64 /usr/local/bin/argocd

argocd version --client
```

Login via CLI (with port-forward running):

```bash
argocd login localhost:8080 \
  --username admin \
  --password '<initial-password>' \
  --insecure

argocd account list
argocd cluster list
```

Change admin password (recommended immediately):

```bash
argocd account update-password \
  --current-password '<initial-password>' \
  --new-password '<your-secure-password>'
```

---

## 8. UI tour — what to notice before Day 2

1. **Applications** — empty until you create an Application (Day 2).
2. **Settings → Repositories** — Git credentials and connection status.
3. **Settings → Clusters** — `https://kubernetes.default.svc` is in-cluster (default).
4. **Settings → Projects** — `default` project exists; restrict in Day 5.
5. **User Info** — RBAC roles appear here after SSO setup.

Sync states you will see throughout the handbook:

| Sync | Meaning |
|------|---------|
| **Synced** | Live matches Git at tracked revision |
| **OutOfSync** | Drift or pending changes |
| **Unknown** | Comparison failed (repo access, manifest error) |

| Health | Meaning |
|--------|---------|
| **Healthy** | All resources pass health checks |
| **Progressing** | Rollout in progress |
| **Degraded** | Failed pods, bad probes, etc. |
| **Missing** | Expected resources not found |

---

## 9. Register the in-cluster destination

Argo CD auto-registers the local cluster. Verify:

```bash
argocd cluster list
# SERVER                          NAME        VERSION  STATUS
# https://kubernetes.default.svc  in-cluster  1.x      Successful
```

For external clusters (Day 6), you install a cluster-scoped agent or add kubeconfig credentials.

---

## 10. Optional — expose server via Ingress

For kind with ingress-nginx from the Kubernetes handbook:

```yaml
# manifests/argocd-ingress.yaml (optional)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server
  namespace: argocd
  annotations:
    nginx.ingress.kubernetes.io/ssl-passthrough: "true"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
spec:
  ingressClassName: nginx
  rules:
    - host: argocd.localdev.me
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: argocd-server
                port:
                  number: 443
```

```bash
kubectl apply -f manifests/argocd-ingress.yaml
# Add to /etc/hosts: 127.0.0.1 argocd.localdev.me
```

---

## 11. Lab — Day 1

1. Create kind cluster `devops-handbook` (or confirm existing).
2. Install Argo CD with the official manifest; wait until all pods in `argocd` are Running.
3. Port-forward `argocd-server` to localhost:8080; log in to the UI as `admin`.
4. Install `argocd` CLI; login with `--insecure`; run `argocd cluster list` and `argocd app list`.
5. Change the admin password via CLI.
6. Draw the control loop: Git → Repo Server → Controller → API Server → cluster.
7. **Stretch:** Install via Helm instead on a second cluster or namespace; compare pod names and CRDs.

**Do not delete Argo CD** — you will use this install for Days 2–7.

---

## 12. DevOps connections

- **Separation of duties:** Developers merge to Git; Argo CD deploys. Fewer people need direct `kubectl` production access.
- **Audit:** Every deploy ties to a Git commit SHA — attach to change tickets and release notes.
- **Disaster recovery:** Reinstall Argo CD and point Applications at the same Git repo to rebuild cluster state (Day 7).

---

## Quick reference

| Task | Command |
|------|---------|
| Install Argo CD | `kubectl apply -n argocd -f …/install.yaml` |
| Pod status | `kubectl get pods -n argocd` |
| Initial password | `kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath=…` |
| Port-forward UI | `kubectl port-forward svc/argocd-server -n argocd 8080:443` |
| CLI login | `argocd login localhost:8080 --insecure` |
| List clusters | `argocd cluster list` |

**Next:** [Day 2 — Your first Application](../day2/)
