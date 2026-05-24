# Helm handbook — design decisions

## Scope

- **7 days** from first `helm install` to production CI/CD and GitOps patterns (not a duplicate of Kubernetes handbook Day 18).
- **Helm 3 only** — no Tiller or Helm 2 migration content.

## Pedagogy

| Day | Rationale |
|-----|-----------|
| 1 | Release lifecycle before authoring charts reduces fear of `helm upgrade`. |
| 2–3 | Structure then templating — matches how engineers read existing charts. |
| 4 | Dependencies after solo charts — avoids subchart confusion on day 2. |
| 5 | Hooks/tests after values merge — hooks need solid template basics. |
| 6 | Packaging once authors can lint and template locally. |
| 7 | Capstone ties chart craft to org workflows (CI, Argo, security). |

## Lab charts

| Chart | Location | Purpose |
|-------|----------|---------|
| `sample-web` | day2/labs, day4/labs (subchart) | Minimal nginx Deployment/Service |
| `template-lab` | day3/labs | `required`, `range`, Ingress guard |
| `umbrella-demo` | day4/labs | file:// subchart + Bitnami redis (optional) |
| `hooks-demo` | day5/labs | post-install Job + `helm test` |

`umbrella-demo` ships `Chart.lock`; run `helm dependency build` if `charts/*.tgz` are missing after clone.

## Edge cases called out in content

- Bitnami chart versions drift — pin `--version` in production; lab redis pinned in `Chart.yaml`.
- Mixing manual Helm upgrades with Argo `selfHeal` causes drift — Day 7 explicit tradeoff.
- Hook failures block releases — prefer GitOps sync waves for migrations at scale.

## User feedback

_(Add notes here as you extend the handbook.)_
