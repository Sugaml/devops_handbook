# Day 7 — Production GitLab CI: HA Runners, Security & Advanced Pipelines

**Goal:** Operate GitLab CI at scale—runner fleets, compliance, parent-child pipelines, and incident response.

**Time:** 5–7 hours

---

## 1. Production checklist

```
[ ] Group/project runners — no shell executor on multi-tenant hosts
[ ] Protected variables only on protected branches
[ ] MR pipelines required before merge
[ ] Container images pinned by digest in deploy manifests
[ ] Runner autoscaling (K8s executor or autoscaler)
[ ] Compliance frameworks enabled (if Ultimate)
[ ] Audit events exported
[ ] Pipeline minutes / runner capacity monitored
```

---

## 2. Runner fleet (Kubernetes)

Helm chart `gitlab/gitlab-runner` on your cluster:

- One pod per job
- Isolation via namespace + network policies
- Cache backed by S3/GCS

---

## 3. Parent-child / multi-project pipelines

**Parent** triggers child in same repo:

```yaml
trigger_child:
  trigger:
    include: .gitlab/ci/build.yml
    strategy: depend
```

**Multi-project** — trigger deploy repo when app builds:

```yaml
trigger_deploy:
  trigger:
    project: mygroup/gitops-deploy
    branch: main
```

---

## 4. `include` and templates

```yaml
include:
  - template: Security/SAST.gitlab-ci.yml
  - local: .gitlab/ci/test.yml
  - project: 'mygroup/ci-templates'
    file: '/templates/docker-build.yml'
```

Centralize org standards; pin template versions.

---

## 5. Security scanning (built-in templates)

```yaml
include:
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Container-Scanning.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml
```

Tune `allow_failure` during adoption; enforce in protected branches later.

---

## 6. Troubleshooting

| Symptom | Action |
|---------|--------|
| Stuck pending | No runner with matching tags; runner offline |
| DinD fails | Privileged mode disabled — use Kaniko |
| Masked var not masked | Value doesn't match masking rules |
| MR pipeline missing | Workflow rules; `rules` too restrictive |
| Cache not hit | Key changed; protected branch mismatch |

**CI/CD logs → Job artifacts → `gitlab-runner verify`**

---

## 7. Lab — Day 7 capstone

1. Split CI into `include: local:` files (test.yml, build.yml).
2. Add SAST template; review one finding (even if allow_failure).
3. Document runner tagging strategy for `dev` vs `prod` jobs.
4. Write runbook: pipeline pending >10 minutes.

---

## 8. Platform comparison

| Feature | GitLab CI | GitHub Actions |
|---------|-----------|----------------|
| Registry | Built-in per project | GHCR separate setup |
| Environments | First-class + review apps | Environments + URLs |
| Runners | GitLab Runner agents | GitHub-hosted / self-hosted |

---

**Prev:** [Day 6](../day6/) · **Track home:** [GitLab README](../README.md)
