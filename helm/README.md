# Helm for DevOps — 7-Day Handbook

A hands-on path from “what is a chart?” to production-grade packaging, upgrades, and CI/CD. Each day builds on the last with commands, patterns, and labs you can run against any Kubernetes cluster.

## Structure

| Day | Topic | Folder |
|-----|--------|--------|
| 1 | Helm concepts, install, repos, first release | [day1](./day1/) |
| 2 | Chart anatomy, `helm create`, local install & upgrade | [day2](./day2/) |
| 3 | Go templates — logic, functions, and safe YAML | [day3](./day3/) |
| 4 | Values, overrides, subcharts & dependencies | [day4](./day4/) |
| 5 | Helpers, hooks, tests, and chart UX | [day5](./day5/) |
| 6 | Package, publish (HTTP/OCI), rollback, tooling | [day6](./day6/) |
| 7 | Production charts, CI/CD, GitOps, security | [day7](./day7/) |

## Prerequisites

- Working Kubernetes cluster (`kind`, `minikube`, or cloud) — see [Kubernetes handbook](../kubernetes/README.md) Day 1–2.
- `kubectl` configured to your cluster context.
- Basic comfort with Deployments, Services, and namespaces.

## How to use this handbook

1. Install Helm 3 (Day 1).
2. Use namespace `helm-handbook` for labs: `kubectl create namespace helm-handbook`.
3. Run every command; use `helm template` before `helm install` when learning.
4. Complete each day's **Lab** before moving on.
5. Keep a personal cheat sheet of `values.yaml` keys you reuse at work.

## Recommended lab setup

```bash
# Helm 3
brew install helm                    # macOS
# Linux: https://helm.sh/docs/intro/install/

helm version

# Cluster (if you do not have one)
kind create cluster --name helm-handbook 2>/dev/null || true
kubectl create namespace helm-handbook

# Charts used in early labs
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
```

## Design notes

- **Helm 3 only** — no Tiller; releases are namespace-scoped secrets (by default).
- Examples favor **declarative values** over long `--set` chains; production uses `-f` or GitOps.
- Sample charts live under each day's `labs/` folder as reference implementations.
- DevOps callouts map Helm skills to CI pipelines, GitOps, and platform engineering.

## Progress checklist

```
[ ] Day 1  [ ] Day 4
[ ] Day 2  [ ] Day 5
[ ] Day 3  [ ] Day 6
[ ] Day 7 — capstone
```

## Related handbooks

| Handbook | Why it matters for Helm |
|----------|-------------------------|
| [Kubernetes](../kubernetes/README.md) | Objects Helm renders (Deployment, Service, Ingress) |
| [Docker](../docker/README.md) | Images referenced in `values.yaml` |
| [Linux](../linux/README.md) | Shell, pipes, and scripting for CI jobs |
