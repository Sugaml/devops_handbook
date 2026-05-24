# Bitbucket Pipelines CI/CD — 7-Day Handbook

YAML-driven CI/CD for Bitbucket Cloud (and Server patterns)—from default branch pipelines to deployment environments, pipes, and Atlassian-integrated delivery.

## Structure

| Day | Topic | Folder |
|-----|--------|--------|
| 1 | Pipelines concepts, enable Pipelines, first YAML | [day1](./day1/) |
| 2 | Steps, parallel steps, caches, services | [day2](./day2/) |
| 3 | Branch pipelines, custom pipelines, schedules | [day3](./day3/) |
| 4 | Variables, secured variables, deployment environments | [day4](./day4/) |
| 5 | Docker builds, ECR/Docker Hub, artifacts | [day5](./day5/) |
| 6 | Pipes, integrations, pull request pipelines | [day6](./day6/) |
| 7 | Production — workspace settings, monorepos, troubleshooting | [day7](./day7/) |

## Prerequisites

- Bitbucket Cloud account (Pipelines included in free tier with minute limits).
- Sample app in a Bitbucket repository.
- Docker familiarity for Day 2+ (Pipelines runs steps in Docker containers).

## Quick start

```bash
# In repo root — bitbucket-pipelines.yml
# Repository settings → Pipelines → Settings → Enable Pipelines
git add bitbucket-pipelines.yml && git push
# Pipelines tab → view build
```

## Progress tracker

```
[ ] Day 1  [ ] Day 4  [ ] Day 7
[ ] Day 2  [ ] Day 5
[ ] Day 3  [ ] Day 6
```

**Start:** [Day 1 — First Bitbucket Pipeline](./day1/)
