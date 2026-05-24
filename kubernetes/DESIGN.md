# Kubernetes Handbook — Design Notes

## Curriculum design

- **30 days** maps to ~1 month of daily study (4–6 hours/day) from zero K8s to production capstone.
- **Progression:** imperative CLI → declarative YAML → platform (RBAC, storage, GitOps) → operations (observability, security, DR).
- **Parity with repo:** Structure mirrors [linux](../linux/README.md) and [docker](../docker/README.md) handbooks (index README + `dayN/README.md`).

## Lab environment choices

- **kind** is the default lab cluster (multi-node, ingress port mapping documented Day 1).
- **minikube** documented as alternative; not all features (e.g. NetworkPolicy) behave identically on kindnet.
- Namespace `handbook-lab` for Days 2–29; `handbook-capstone` for Day 30 isolation.

## Edge cases documented in content

- kind NetworkPolicy enforcement may require Calico (Day 15).
- metrics-server on kind often needs `--kubelet-insecure-tls` patch (Day 10, 20).
- RWO volumes block multi-replica Deployments sharing one PVC (Day 16 lab).
- Pod Security `restricted` may not fully apply on all kind configs (Day 26).

## Performance / scope

- Each day is self-contained README (~150–350 lines) to avoid a single unmaintainable file.
- Sample YAML in Day 30 README is copy-paste ready; optional `manifests/` subfolder can be added by learners during capstone.

## User feedback / future enhancements

- Add `day30/manifests/` split files if learners want `kubectl apply -R` without copy-paste.
- Video walkthrough links per week (external).
- Kustomize overlay track parallel to raw YAML days.
