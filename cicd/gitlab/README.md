# GitLab CI/CD — 7-Day Handbook

All-in-one pipelines with `.gitlab-ci.yml`, runners, environments, and review apps—from hello pipeline to group-level runner fleets and compliance-ready delivery.

## Structure

| Day | Topic | Folder |
|-----|--------|--------|
| 1 | GitLab CI concepts, first `.gitlab-ci.yml` | [day1](./day1/) |
| 2 | Stages, jobs, rules, needs, DAG pipelines | [day2](./day2/) |
| 3 | Runners — shared, specific, shell, Docker, Kubernetes | [day3](./day3/) |
| 4 | Variables, protected branches, CI/CD settings | [day4](./day4/) |
| 5 | Docker builds, registry, cache, artifacts | [day5](./day5/) |
| 6 | Environments, review apps, deployment jobs | [day6](./day6/) |
| 7 | Production — HA runners, security, parent-child pipelines | [day7](./day7/) |

## Prerequisites

- GitLab.com account or self-managed GitLab 16+.
- Sample app in a GitLab project.
- GitLab Runner installed locally for Day 3+ (optional: use shared SaaS runners).

## Quick start

```bash
# Register a local runner (GitLab.com — get token from Settings → CI/CD → Runners)
gitlab-runner register \
  --url https://gitlab.com \
  --token YOUR_REGISTRATION_TOKEN \
  --executor docker \
  --docker-image alpine:latest \
  --description "handbook-local"
```

## Progress tracker

```
[ ] Day 1  [ ] Day 4  [ ] Day 7
[ ] Day 2  [ ] Day 5
[ ] Day 3  [ ] Day 6
```

**Start:** [Day 1 — First GitLab pipeline](./day1/)
