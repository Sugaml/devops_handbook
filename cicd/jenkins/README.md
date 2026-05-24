# Jenkins CI/CD — 7-Day Handbook

Self-hosted, plugin-rich CI/CD from first freestyle job to production-grade declarative pipelines, multibranch workflows, and controller hardening.

## Structure

| Day | Topic | Folder |
|-----|--------|--------|
| 1 | CI/CD fundamentals, install Jenkins, first job | [day1](./day1/) |
| 2 | Declarative Pipeline syntax, Jenkinsfile, stages | [day2](./day2/) |
| 3 | Agents, labels, Docker agents, parallelism | [day3](./day3/) |
| 4 | Credentials, environment variables, secret patterns | [day4](./day4/) |
| 5 | Docker builds, artifacts, registry push | [day5](./day5/) |
| 6 | Multibranch pipelines, webhooks, PR builds | [day6](./day6/) |
| 7 | Production — HA, RBAC, security, troubleshooting | [day7](./day7/) |

## Prerequisites

- Docker (recommended for local Jenkins LTS).
- Git and a GitHub/GitLab/Bitbucket remote for multibranch labs (Day 6+).
- Sample app: [../labs/sample-web](../labs/sample-web/)

## Quick start

```bash
docker volume create jenkins_home
docker run -d --name jenkins \
  -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  jenkins/jenkins:lts-jdk17

docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
# Open http://localhost:8080 — install suggested plugins
```

## Progress tracker

```
[ ] Day 1  [ ] Day 4  [ ] Day 7
[ ] Day 2  [ ] Day 5
[ ] Day 3  [ ] Day 6
```

**Start:** [Day 1 — CI/CD basics & first Jenkins job](./day1/)
