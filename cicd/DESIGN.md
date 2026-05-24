# CI/CD Handbook — Design & curriculum notes

## Goals

- **Four parallel tracks** with identical learning arc so learners can compare Jenkins, GitHub Actions, GitLab CI, and Bitbucket Pipelines.
- **Basic → professional**: Day 1 is concepts + first green build; Day 7 is HA, security, audit, and incident response.
- **Same sample app** across tracks to isolate platform syntax and operational differences.
- **Runnable labs**: Every day ends with a lab that produces a verifiable outcome (green pipeline, pushed image, deployed env).

## Pedagogy

| Pattern | Usage |
|---------|--------|
| Goal + time box | 4–6 hours/day theory + hands-on |
| Concept → syntax → lab | Platform-agnostic CI/CD idea first, then tool-specific YAML |
| Comparison tables | Jenkins vs cloud-native triggers, shared vs self-hosted runners |
| DevOps callout | Branch protection, OIDC, least privilege, immutable artifacts |
| Production checklist | Day 7 capstone per platform |
| Prev/Next links | Linear path within each track |

## Curriculum mapping (all platforms)

| Day | CI/CD concept | Jenkins | GitHub | GitLab | Bitbucket |
|-----|---------------|---------|--------|--------|-----------|
| 1 | Pipeline anatomy | Freestyle + intro | First workflow | `.gitlab-ci.yml` | `bitbucket-pipelines.yml` |
| 2 | Stages & quality gates | Declarative stages | Jobs/steps + PR | Stages/jobs/rules | Steps + default pipeline |
| 3 | Execution environment | Agents/labels | Runners + matrix | Runners/tags | Docker image + size |
| 4 | Secrets & envs | Credentials binding | Secrets + envs | CI variables + protected | Repository/deployment vars |
| 5 | Artifacts & containers | Docker agent + ECR | build-push-action | Kaniko/registry | Docker service + ECR pipe |
| 6 | Branch/PR workflows | Multibranch | PR + reusable wf | Review apps | Branch pipelines + pipes |
| 7 | Production ops | Controller HA, RBAC | Org policies, OIDC | Group runners, compliance | Workspace settings, audit |

## Edge cases documented

- **Fork PRs and secrets**: GitHub/GitLab/Bitbucket do not expose secrets to fork PRs by default — document safe patterns (pull_request_target pitfalls called out on GitHub Day 6).
- **Docker-in-Docker vs Kaniko vs buildkit**: Trade-offs on Day 5 each track.
- **Cache poisoning**: Scoped caches, lockfiles, content-addressable keys (Day 3).
- **Long-running pipelines**: Timeouts, `when: manual`, deployment gates (Day 4–6).
- **Monorepos**: Path filters, `rules:changes`, `paths-filter` action, Bitbucket changesets (Day 6–7).
- **Air-gapped / self-hosted**: Jenkins agents, self-hosted runners, GitLab runner on private network (Day 3, 7).

## Security baseline (Day 7 themes)

- Pin third-party actions/images/plugins to SHA or semver ranges with renovate.
- OIDC to cloud (AWS/GCP/Azure) instead of long-lived cloud keys where supported.
- Separate CI and CD credentials; production deploys from protected branches only.
- Audit logs and artifact retention policies.

## Performance optimizations

- Dependency caching (npm/pip/maven) with lockfile-keyed cache keys.
- Parallel jobs/stages where tests are independent.
- Fail fast: lint before integration tests.
- Conditional jobs (`rules`, `if:`, `changeset`) to skip unrelated work.

## User feedback / iteration

- Add Azure DevOps track if requested.
- Optional Tekton/Argo Workflows module for Kubernetes-native CI (links to Kubernetes/Argo handbooks).
- Expand cloud deploy labs (ECS, Cloud Run, AKS) as companion snippets in Day 5–6.

## Versioning

- Jenkins LTS 2.4xx+, JDK 17.
- GitHub Actions: `actions/checkout@v4`, `setup-python@v5`, `docker/build-push-action@v6`.
- GitLab CI schema compatible with GitLab 16.x–17.x.
- Bitbucket Pipelines: Cloud YAML v2; Server/Data Center notes where different.
