# GitHub Actions CI/CD — 7-Day Handbook

Build, test, and deploy from GitHub-native YAML workflows—from your first `workflow_dispatch` to reusable workflows, OIDC cloud auth, and organization-scale governance.

## Structure

| Day | Topic | Folder |
|-----|--------|--------|
| 1 | CI/CD on GitHub, first workflow, triggers | [day1](./day1/) |
| 2 | Jobs, steps, PR workflows, status checks | [day2](./day2/) |
| 3 | Matrix builds, caching, concurrency | [day3](./day3/) |
| 4 | Secrets, environments, deployment protection | [day4](./day4/) |
| 5 | Docker build & push, artifacts, registries | [day5](./day5/) |
| 6 | Reusable workflows, composite actions, self-hosted runners | [day6](./day6/) |
| 7 | Production — org policies, security, monorepos | [day7](./day7/) |

## Prerequisites

- GitHub account (free tier works).
- Sample app pushed to a repository you control.
- Docker Hub or GHCR account for Day 5 (optional: local `docker load` only).

## Quick start

```bash
mkdir -p my-app/.github/workflows
# Copy day1/labs/ci.yml into your repo
git add . && git commit -m "ci: add first workflow"
git push
# Actions tab → watch the run
```

## Progress tracker

```
[ ] Day 1  [ ] Day 4  [ ] Day 7
[ ] Day 2  [ ] Day 5
[ ] Day 3  [ ] Day 6
```

**Start:** [Day 1 — First GitHub Actions workflow](./day1/)
