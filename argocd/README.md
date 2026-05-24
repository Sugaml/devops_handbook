# Argo CD for DevOps — 7-Day Handbook

A practical, CLI-first path from GitOps fundamentals to production-grade Argo CD operations. Each day builds on the previous one with manifests, commands, and labs you can run on **kind**, **minikube**, or any conformant cluster.

## Prerequisites

- Comfortable Linux CLI ([Linux handbook](../linux/README.md) Days 1–3 recommended).
- Kubernetes fundamentals ([Kubernetes handbook](../kubernetes/README.md) Days 1–7 recommended).
- Helm basics ([Helm handbook](../helm/README.md) Days 1–2 recommended).
- A machine with **8 GB+ RAM** for local clusters (kind/minikube).
- **Git** installed and a GitHub/GitLab account (or local bare repo for offline labs).

## Structure

| Day | Topic | Folder |
|-----|--------|--------|
| 1 | GitOps, Argo CD architecture, install & first login | [day1](./day1/) |
| 2 | Applications, Git sources, manual sync & CLI | [day2](./day2/) |
| 3 | Sync policies, health, hooks & drift control | [day3](./day3/) |
| 4 | Helm, Kustomize & multi-source applications | [day4](./day4/) |
| 5 | AppProjects, RBAC, repos & credentials | [day5](./day5/) |
| 6 | ApplicationSets & multi-cluster patterns | [day6](./day6/) |
| 7 | Production GitOps — HA, DR, CI/CD, troubleshooting | [day7](./day7/) |

## How to use this handbook

1. **Create a lab cluster once** (Day 1) and reuse it; Argo CD stays installed in `argocd` namespace.
2. Apply every manifest yourself; use `argocd app diff` and `--dry-run` before risky changes.
3. Complete each day's **Lab** before advancing — labs use a sample Git repo layout under `labs/`.
4. Keep a personal GitOps repo — what you build in 7 days becomes your interview and portfolio kit.

## Recommended lab setup

```bash
# kind (Kubernetes IN Docker) — recommended
brew install kind kubectl helm argocd   # macOS; use package manager on Linux
kind create cluster --name devops-handbook

kubectl cluster-info
kubectl get nodes -o wide
```

Install these tools early; they appear throughout the curriculum:

| Tool | Purpose |
|------|---------|
| `kubectl` | Cluster CLI |
| `kind` or `minikube` | Local cluster |
| `helm` | Install Argo CD and sample charts |
| `argocd` | Argo CD CLI (Day 1+) |
| `kustomize` | Overlay labs (Day 4+) |
| `git` | Source of truth for GitOps |

## GitOps repo layout (used across all days)

Create or fork a repo with this structure — labs reference it:

```
gitops-handbook/
├── apps/
│   ├── guestbook/
│   │   └── base/          # plain manifests or kustomization
│   └── helm-nginx/
│       └── values.yaml
├── bootstrap/
│   └── root-app.yaml      # App-of-Apps (Day 2+)
├── projects/
│   └── handbook.yaml
└── clusters/
    └── dev/
        └── kustomization.yaml
```

For local-only labs, a bare repo on your machine works:

```bash
mkdir -p ~/gitops-handbook && cd ~/gitops-handbook
git init
# ... add files from each day's labs/
```

## Design notes

- Examples target **Argo CD 2.10+** and Kubernetes **1.28+**.
- Argo CD installs into namespace `argocd`; sample apps use `handbook-lab`.
- Production callouts explain what changes on EKS, GKE, AKS, and self-managed clusters.
- Sample YAML lives in each day's `manifests/` or `labs/` folder.

## Progress tracker

```
[ ] Day 1  GitOps & install
[ ] Day 2  First Application
[ ] Day 3  Sync policies & health
[ ] Day 4  Helm & Kustomize
[ ] Day 5  Projects & RBAC
[ ] Day 6  ApplicationSets
[ ] Day 7  Production patterns
```
