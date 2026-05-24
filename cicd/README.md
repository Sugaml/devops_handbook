# CI/CD for DevOps — 7-Day Handbook (4 Platforms)

A practical, hands-on path from CI/CD fundamentals to production-grade pipelines on **Jenkins**, **GitHub Actions**, **GitLab CI**, and **Bitbucket Pipelines**. Each platform has its own 7-day track; all tracks share the same learning arc so you can compare tools or specialize in one.

## Prerequisites

- Comfortable Linux/macOS terminal ([Linux handbook](../linux/README.md) Days 1–3).
- Git fundamentals ([Git handbook](../git/README.md) Days 1–4).
- Basic Docker ([Docker handbook](../docker/README.md) Day 1–2) for build-and-push labs (Day 5 on each track).
- A GitHub, GitLab, or Bitbucket account (free tier is enough).
- For Jenkins: Docker or a VM with 4 GB+ RAM.

## Choose your track

| Platform | Best for | Folder |
|----------|----------|--------|
| **Jenkins** | Self-hosted, maximum flexibility, legacy-to-modern migration | [jenkins](./jenkins/) |
| **GitHub Actions** | GitHub-native repos, OSS, marketplace ecosystem | [github](./github/) |
| **GitLab CI** | All-in-one DevOps platform, built-in registry & environments | [gitlab](./gitlab/) |
| **Bitbucket Pipelines** | Atlassian stack (Jira, Confluence), Bitbucket Cloud/Server | [bitbucket](./bitbucket/) |

You can complete **one track in 7 days** or run **all four in parallel** (same day = same concept, different syntax).

## Shared 7-day arc

| Day | Topic | What you build |
|-----|--------|----------------|
| 1 | CI/CD concepts, first pipeline, anatomy of a build | Hello-world build on push |
| 2 | Triggers, stages, jobs, and workflow structure | Lint + test on PR |
| 3 | Runners/agents, parallelism, caching | Faster pipelines with cache |
| 4 | Secrets, credentials, environments | Deploy to staging with secrets |
| 5 | Docker build, registry push, artifacts | Build image tagged with commit SHA |
| 6 | Multi-branch, review apps, advanced triggers | PR pipelines + optional preview |
| 7 | Production hardening, security, troubleshooting | HA, RBAC, audit-ready pipeline |

## Sample application (used in all tracks)

Each track uses the same sample app so you focus on CI/CD, not application code:

```
sample-web/
├── src/
│   └── app.py          # Flask hello-world
├── tests/
│   └── test_app.py     # pytest
├── Dockerfile
├── requirements.txt
└── README.md
```

Copy from any track's `day1/labs/sample-web/` or scaffold inline (Day 1 labs include commands).

## How to use this handbook

1. Pick **one platform** and follow Day 1 → Day 7 in order.
2. Run every pipeline yourself; break things on purpose (wrong secret name, failing test) and read logs.
3. Complete each day's **Lab** before advancing.
4. On Day 7, compare your pipeline to the **production checklist** in that day's README.
5. Optional capstone: implement the same app pipeline on a second platform and diff the YAML.

## Recommended local setup

```bash
# Universal
git --version
docker --version    # Day 5+
python3 --version   # sample app

# Jenkins (Day 1+)
docker run -d --name jenkins -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  jenkins/jenkins:lts-jdk17

# GitHub CLI (optional)
# brew install gh && gh auth login

# GitLab Runner (local, Day 3+ GitLab track)
# brew install gitlab-runner   # macOS
# gitlab-runner register        # follow prompts
```

## Design notes

- Examples target **2025–2026** stable releases (Jenkins LTS, Actions v4 checkout, GitLab 16+, Bitbucket Cloud Pipelines).
- Secrets are always **placeholders** — never commit real tokens; use platform secret stores.
- Production callouts cover least privilege, branch protection, and supply-chain basics (SBOM, pinned actions/images).
- Lab YAML and Jenkinsfiles live under each day's `labs/` folder.

## Progress tracker

```
Jenkins:   [ ] D1 [ ] D2 [ ] D3 [ ] D4 [ ] D5 [ ] D6 [ ] D7
GitHub:    [ ] D1 [ ] D2 [ ] D3 [ ] D4 [ ] D5 [ ] D6 [ ] D7
GitLab:    [ ] D1 [ ] D2 [ ] D3 [ ] D4 [ ] D5 [ ] D6 [ ] D7
Bitbucket: [ ] D1 [ ] D2 [ ] D3 [ ] D4 [ ] D5 [ ] D6 [ ] D7
```

## Related handbooks

- [Git](../git/README.md) — branching, hooks, and PR workflows that trigger CI
- [Docker](../docker/README.md) — images built in Day 5
- [Kubernetes](../kubernetes/README.md) — deploy targets for Day 6–7
- [Argo CD](../argocd/README.md) — GitOps delivery after CI builds artifacts
