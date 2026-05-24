# Argo CD Handbook — Design & curriculum notes

## Goals

- **CLI-first**: Every day is actionable from a terminal; UI steps are mentioned for orientation but automation is the default.
- **DevOps trajectory**: Days 1–2 (GitOps mental model + first app) → 3–4 (sync semantics + packaging) → 5–6 (governance + scale) → 7 (production hardening).
- **Topic coverage**: GitOps principles, Application CR, sync/prune/self-heal, Helm/Kustomize, AppProjects, RBAC, repos/credentials, ApplicationSets, multi-cluster, HA, DR, observability, CI integration, secrets patterns.

## Pedagogy

| Pattern | Usage |
|---------|--------|
| Goal + time box | Sets expectations (4–6 h/day) |
| Tables | Compare sync modes, health states, generator types |
| ASCII diagrams | Control loop, App-of-Apps, multi-cluster |
| Code blocks | Runnable `kubectl`, `argocd`, `helm` commands |
| DevOps callout | CI promotion, least privilege, blast radius |
| Lab | Creates + verifies + **teardown** where safe |
| Prev/Next links | Linear path through 7 days |

## Edge cases documented in days

- **OutOfSync vs Synced**: Manual edits, ignored fields, `ignoreDifferences` (Day 3).
- **Prune ordering**: Finalizers, foreground deletion, `--prune-last` (Day 3).
- **Helm `--release-name`**: Multiple apps from one chart repo (Day 4).
- **Project `sourceRepos` whitelist**: Prevents deploying from arbitrary Git URLs (Day 5).
- **ApplicationSet owner references**: Deleting generator app vs child apps (Day 6).
- **Repo server credentials rotation**: Requires pod restart or credential template update (Day 5, 7).

## Performance / operational optimizations

- **Repo server caching** and **manifest generate cache** for large monorepos (Day 7).
- **Application controller sharding** for 1000+ apps (Day 7).
- **Sync waves** and **hooks** instead of sleep in CI (Day 3).
- **OCI Helm registries** as first-class sources (Day 4).

## User feedback / iteration

- Optional add-on: **Argo Rollouts** companion track (canary/blue-green) after Day 7.
- Optional add-on: **Argo Workflows** / **Argo Events** for pipeline orchestration.
- Extend Day 5 with Dex + OIDC provider-specific snippets when users request GitHub/Google SSO labs.

## Versioning

- Written for Argo CD 2.10+ and APIs as of 2025–2026; verify deprecated flags with `argocd version` and [upstream docs](https://argo-cd.readthedocs.io/).
