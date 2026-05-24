# Kubernetes for DevOps — 30-Day Handbook

A practical, CLI-first path from Kubernetes fundamentals to production-grade platform engineering. Each day builds on the previous one with manifests, commands, and labs you can run on **kind**, **minikube**, or any conformant cluster.

## Prerequisites

- Comfortable Linux CLI ([Linux handbook](../linux/README.md) Days 1–3 recommended).
- Containers and images ([Docker handbook](../docker/README.md) Days 1–2 recommended).
- A machine with **8 GB+ RAM** for local clusters (kind/minikube).

## Structure

### Week 1 — Foundations (Days 1–7)

| Day | Topic | Folder |
|-----|--------|--------|
| 1 | Architecture, control plane, cluster bootstrap | [day1](./day1/) |
| 2 | kubectl, contexts, namespaces, API objects | [day2](./day2/) |
| 3 | Pods — lifecycle, multi-container, debugging | [day3](./day3/) |
| 4 | Labels, selectors, annotations | [day4](./day4/) |
| 5 | Deployments and rolling updates | [day5](./day5/) |
| 6 | Services — ClusterIP, NodePort, LoadBalancer | [day6](./day6/) |
| 7 | Ingress and HTTP routing | [day7](./day7/) |

### Week 2 — Configuration & resources (Days 8–14)

| Day | Topic | Folder |
|-----|--------|--------|
| 8 | ConfigMaps and configuration patterns | [day8](./day8/) |
| 9 | Secrets and sensitive data | [day9](./day9/) |
| 10 | Requests, limits, QoS, ResourceQuota | [day10](./day10/) |
| 11 | StatefulSets and stable identity | [day11](./day11/) |
| 12 | DaemonSets, Jobs, CronJobs | [day12](./day12/) |
| 13 | RBAC — roles, bindings, least privilege | [day13](./day13/) |
| 14 | Service accounts and API access | [day14](./day14/) |

### Week 3 — Storage, packaging, reliability (Days 15–21)

| Day | Topic | Folder |
|-----|--------|--------|
| 15 | NetworkPolicies and pod networking | [day15](./day15/) |
| 16 | PersistentVolumes and PVCs | [day16](./day16/) |
| 17 | StorageClasses and dynamic provisioning | [day17](./day17/) |
| 18 | Helm — charts, values, releases | [day18](./day18/) |
| 19 | Probes — liveness, readiness, startup | [day19](./day19/) |
| 20 | HPA, VPA concepts, cluster autoscaling | [day20](./day20/) |
| 21 | Init containers, sidecars, patterns | [day21](./day21/) |

### Week 4 — Production platform (Days 22–30)

| Day | Topic | Folder |
|-----|--------|--------|
| 22 | CRDs, operators, custom controllers | [day22](./day22/) |
| 23 | GitOps — Argo CD / Flux workflows | [day23](./day23/) |
| 24 | Cluster lifecycle — upgrades, backups, DR | [day24](./day24/) |
| 25 | Observability — metrics, logs, traces | [day25](./day25/) |
| 26 | Security — admission, Pod Security, supply chain | [day26](./day26/) |
| 27 | Troubleshooting methodology | [day27](./day27/) |
| 28 | Multi-tenancy, namespaces, quotas at scale | [day28](./day28/) |
| 29 | Production checklist and certification prep | [day29](./day29/) |
| 30 | Capstone — full stack on Kubernetes | [day30](./day30/) |

## How to use this handbook

1. **Create a lab cluster once** (Day 1) and reuse it; reset namespaces between labs if needed.
2. Apply every manifest yourself; use `kubectl explain` and `--dry-run=client` liberally.
3. Complete each day's **Lab** before advancing.
4. Keep a personal manifest repo — what you build in 30 days becomes your interview/portfolio kit.

## Recommended lab setup

```bash
# kind (Kubernetes IN Docker) — recommended
brew install kind kubectl helm   # macOS; use package manager on Linux
kind create cluster --name devops-handbook
kubectl cluster-info
kubectl get nodes -o wide

# Alternative: minikube
# minikube start --cpus=4 --memory=8192
```

Install these tools early; they appear throughout the curriculum:

| Tool | Purpose |
|------|---------|
| `kubectl` | Cluster CLI |
| `kind` or `minikube` | Local cluster |
| `helm` | Package manager (Day 18+) |
| `k9s` | Optional TUI for exploration |
| `kubectx` / `kubens` | Optional context/namespace switching |

## Design notes

- Manifests use `apiVersion` values current for Kubernetes 1.28+ unless noted.
- Examples use namespace `handbook-lab` where isolation helps; create it on Day 2.
- Production callouts explain what changes on EKS, GKE, AKS, and bare metal.
- Labs are self-contained; sample YAML lives in each day's folder under `manifests/` where files are referenced.

## Progress tracker

Copy this into your notes and check off days as you complete labs:

```
[ ] Day 1  [ ] Day 11 [ ] Day 21
[ ] Day 2  [ ] Day 12 [ ] Day 22
[ ] Day 3  [ ] Day 13 [ ] Day 23
[ ] Day 4  [ ] Day 14 [ ] Day 24
[ ] Day 5  [ ] Day 15 [ ] Day 25
[ ] Day 6  [ ] Day 16 [ ] Day 26
[ ] Day 7  [ ] Day 17 [ ] Day 27
[ ] Day 8  [ ] Day 18 [ ] Day 28
[ ] Day 9  [ ] Day 19 [ ] Day 29
[ ] Day 10 [ ] Day 20 [ ] Day 30
```
