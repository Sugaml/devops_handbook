# Day 6 — ApplicationSets & Multi-Cluster GitOps

**Goal:** Generate many Applications from templates using ApplicationSet controllers, manage multiple clusters, and implement scalable App-of-Apps patterns.

**Time:** 5–6 hours

---

## 1. ApplicationSet vs Application

| Application | ApplicationSet |
|-------------|----------------|
| One app, one source, one destination | Template × generator = N Applications |
| Manual copy for each env/cluster | DRY — add cluster to Git, app appears |
| Good for single deployables | Good for fleets, tenants, monorepos |

```
ApplicationSet (guestbook-set)
    │
    ├── generator: git directories → apps/*
    │
    └── template → Application per directory
              ├── guestbook-dev
              ├── guestbook-staging
              └── guestbook-prod
```

Install ApplicationSet controller (included in standard install.yaml since Argo CD 2.3+):

```bash
kubectl get crd applicationsets.argoproj.io
kubectl get pods -n argocd -l app.kubernetes.io/name=argocd-applicationset-controller
```

---

## 2. Generator types

| Generator | Creates apps from |
|-----------|-------------------|
| **List** | Static list of elements |
| **Cluster** | Registered Argo CD clusters |
| **Git** | Directories or files in repo |
| **Matrix** | Cartesian product of two generators |
| **Merge** | Merge generator outputs |
| **SCM Provider** | GitHub/GitLab org repos |
| **Cluster Decision** | Custom plugin |
| **Pull Request** | Preview envs per PR |

---

## 3. List generator — multi-environment

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: guestbook-envs
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - env: dev
            namespace: handbook-lab
            replicas: "1"
          - env: staging
            namespace: handbook-staging
            replicas: "2"
  template:
    metadata:
      name: 'guestbook-{{env}}'
    spec:
      project: handbook
      source:
        repoURL: https://github.com/argoproj/argocd-example-apps.git
        targetRevision: HEAD
        path: guestbook
        helm:
          parameters:
            - name: replicaCount
              value: '{{replicas}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

Apply:

```bash
kubectl apply -f manifests/applicationset-list.yaml
kubectl get applicationsets -n argocd
argocd app list | grep guestbook
```

---

## 4. Git directory generator — monorepo

Repo layout:

```
apps/
├── api/
│   └── kustomization.yaml
├── web/
│   └── kustomization.yaml
└── worker/
    └── kustomization.yaml
```

```yaml
spec:
  generators:
    - git:
        repoURL: https://github.com/YOUR_ORG/gitops-handbook.git
        revision: main
        directories:
          - path: apps/*
  template:
    metadata:
      name: '{{path.basename}}'
    spec:
      project: handbook
      source:
        repoURL: https://github.com/YOUR_ORG/gitops-handbook.git
        targetRevision: main
        path: '{{path}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: handbook-lab
```

Add `apps/payments/` → Application `payments` appears automatically.

---

## 5. Cluster generator — multi-cluster

Register a second cluster (e.g. staging EKS):

```bash
argocd cluster add staging-context --name staging-eks
argocd cluster list
```

```yaml
spec:
  generators:
    - clusters:
        selector:
          matchLabels:
            env: non-prod
  template:
    metadata:
      name: '{{name}}-guestbook'
    spec:
      source:
        repoURL: https://github.com/argoproj/argocd-example-apps.git
        path: guestbook
      destination:
        server: '{{server}}'
        namespace: guestbook
```

Label clusters when adding:

```bash
argocd cluster set https://STAGING_API --label env=non-prod
```

**Production:** One Argo CD management cluster deploys to many workload clusters — hub-spoke GitOps.

---

## 6. Matrix generator

Deploy every service to every cluster:

```yaml
spec:
  generators:
    - matrix:
        generators:
          - git:
              repoURL: https://github.com/YOUR_ORG/gitops-handbook.git
              revision: main
              directories:
                - path: apps/*
          - clusters:
              selector:
                matchLabels:
                  region: us-east
  template:
    metadata:
      name: '{{path.basename}}-{{name}}'
    spec:
      source:
        repoURL: https://github.com/YOUR_ORG/gitops-handbook.git
        path: '{{path}}'
      destination:
        server: '{{server}}'
        namespace: '{{path.basename}}'
```

---

## 7. App-of-Apps vs ApplicationSet

| Pattern | When |
|---------|------|
| **App-of-Apps** | Simple bootstrap; few apps; explicit YAML per app |
| **ApplicationSet** | Many apps; dynamic clusters; monorepo directories |

Both can coexist — bootstrap root app installs ApplicationSets.

```yaml
# bootstrap/root.yaml → points to applicationsets/ folder
```

---

## 8. Progressive syncs and rollout (preview)

ApplicationSet sync policy (Argo CD 2.9+):

```yaml
spec:
  strategy:
    type: RollingSync
    rollingSync:
      steps:
        - matchExpressions:
            - key: env
              operator: In
              values: [dev]
        - matchExpressions:
            - key: env
              operator: In
              values: [staging]
        - matchExpressions:
            - key: env
              operator: In
              values: [prod]
```

Pairs with **Argo Rollouts** for canary analysis (post-handbook track).

---

## 9. Pull request generator (preview environments)

```yaml
generators:
  - pullRequest:
      github:
        owner: YOUR_ORG
        repo: microservice
        tokenRef:
          secretName: github-token
          key: token
      requeueAfterSeconds: 180
template:
  metadata:
    name: 'pr-{{number}}'
  spec:
    source:
      targetRevision: '{{head_sha}}'
      path: deploy/overlays/preview
    destination:
      namespace: 'pr-{{number}}'
```

Delete Application when PR closes — keeps cluster clean.

---

## 10. Lab — Day 6

1. Apply `manifests/applicationset-list.yaml`; verify two Applications created.
2. Add a third element to the list generator; confirm a third Application appears.
3. Set up Git directory generator against `labs/apps/*` (copy sample dirs).
4. Register a second cluster (optional: `kind create cluster --name handbook-staging` + `argocd cluster add`).
5. Label clusters and apply cluster generator template.
6. Delete an ApplicationSet — observe child Application cleanup behavior.
7. **Stretch:** Matrix generator combining two apps × two namespaces.

---

## 11. DevOps connections

- **Onboarding:** New microservice = new folder in Git — ApplicationSet creates Argo CD app without ticket to platform team.
- **Multi-cluster:** Single pane in Argo CD UI for dev/staging/prod across regions.
- **PR previews:** ApplicationSet + PR generator replaces manual namespace-per-developer scripts.

---

## Quick reference

| Task | Command |
|------|---------|
| List ApplicationSets | `kubectl get applicationsets -n argocd` |
| Generated apps | `argocd app list -l app.kubernetes.io/instance` |
| Add cluster | `argocd cluster add CONTEXT --name NAME` |
| Cluster labels | `argocd cluster set SERVER --label key=val` |

**Previous:** [Day 5](../day5/) · **Next:** [Day 7 — Production GitOps](../day7/)
