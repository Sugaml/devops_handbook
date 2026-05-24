# Day 23 — GitOps: Argo CD & Flux

**Goal:** Deploy and manage cluster state from Git repositories using GitOps principles, install Argo CD, and sync an application.

**Time:** 6 hours

---

## 1. GitOps principles

| Principle | Meaning |
|-----------|---------|
| **Declarative** | Desired state in Git (YAML/Helm/Kustomize) |
| **Versioned** | Git history = audit trail |
| **Automated** | Controller reconciles cluster ↔ Git |
| **Continuous** | Drift detection and self-heal |

Anti-pattern: `kubectl apply` from laptop as primary deploy path.

---

## 2. Pull vs push deploy

```
Push (CI):  CI ──kubectl apply──▶ Cluster
Pull (GitOps): CI ──commit──▶ Git ◀──watch── Argo CD/Flux ──▶ Cluster
```

GitOps agents run inside cluster with deploy RBAC.

---

## 3. Install Argo CD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=300s
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Initial admin password
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath='{.data.password}' | base64 -d; echo
```

Login UI: https://localhost:8080 (user `admin`).

CLI:

```bash
brew install argocd
argocd login localhost:8080 --username admin --password PASS --insecure
```

---

## 4. Argo CD Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: handbook-web
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/handbook-apps.git
    targetRevision: main
    path: apps/web
  destination:
    server: https://kubernetes.default.svc
    namespace: handbook-lab
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

```bash
kubectl apply -f application.yaml
argocd app get handbook-web
argocd app sync handbook-web
```

---

## 5. Flux (alternative)

```bash
flux install
flux create source git handbook \
  --url=https://github.com/your-org/handbook-apps \
  --branch=main
flux create kustomization handbook-web \
  --source=handbook \
  --path=./apps/web \
  --prune=true \
  --interval=1m
```

Flux uses GitRepository + Kustomization/HelmRelease CRDs.

---

## 6. Kustomize overlays (common with GitOps)

```
apps/web/
  base/
    deployment.yaml
    service.yaml
    kustomization.yaml
  overlays/
    dev/
      kustomization.yaml   # patches, namespace
    prod/
      kustomization.yaml
```

```bash
kubectl kustomize apps/web/overlays/dev | kubectl apply -f -
```

---

## 7. Lab — Day 23

1. Install Argo CD on kind cluster.
2. Create local Git repo with simple nginx Deployment manifest.
3. Register repo in Argo CD (public repo or file:// via config map for lab).
4. Create Application; sync; verify resources in `handbook-lab`.
5. Change replica count in Git; observe auto-sync (if enabled) or manual sync.
6. `kubectl scale` deployment manually; enable selfHeal; watch Argo revert drift.

**Stretch:** Compare Flux bootstrap vs Argo CD app-of-apps pattern.

---

## 8. DevOps connections

- **Secrets:** Sealed Secrets, SOPS, External Secrets with GitOps.
- **Promotions:** dev branch → staging → prod via PR merges and overlays.
- **Rollback:** Git revert + sync faster than `kubectl rollout undo` across many resources.

---

## Quick reference

| Task | Command |
|------|---------|
| Argo apps | `argocd app list` |
| Sync | `argocd app sync NAME` |
| Diff | `argocd app diff NAME` |
| Flux status | `flux get kustomizations` |

**Next:** [Day 24 — Cluster lifecycle](../day24/)
