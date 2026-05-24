# Day 3 — GitLab Runners: Shared, Specific & Executors

**Goal:** Register and use project/group runners, choose executors (Docker, shell, Kubernetes), and route jobs with tags.

**Time:** 5–6 hours

---

## 1. Runner types

| Type | Who pays / manages | Typical use |
|------|-------------------|-------------|
| **Shared (SaaS)** | GitLab.com shared pool | OSS, small projects |
| **Group runner** | Your org | Many projects in group |
| **Project runner** | Single project | Dedicated, secrets isolation |
| **Self-managed** | You on VM/K8s | Private network, custom hardware |

---

## 2. Register a Docker runner (local lab)

```bash
# GitLab.com: Settings → CI/CD → Runners → New project runner
gitlab-runner register \
  --url https://gitlab.com \
  --token glrt-XXXX \
  --executor docker \
  --docker-image python:3.12-slim \
  --description "handbook-docker" \
  --tag-list "docker,handbook"
```

```bash
gitlab-runner verify
gitlab-runner run  # or install as service
```

---

## 3. Tags in jobs

```yaml
test:
  tags:
    - docker
    - handbook
  image: python:3.12-slim
  script:
    - pytest -v
```

Untagged jobs won't run on tagged-only runners.

---

## 4. Executors compared

| Executor | Isolation | Notes |
|----------|-----------|-------|
| **docker** | Container per job | Most common |
| **shell** | Runs on host | Fast; least isolation |
| **kubernetes** | Pod per job | Scales on K8s |
| **docker+machine** | Auto-scale VMs | Legacy pattern on AWS |

---

## 5. Runner security

- **Protected runners** — only protected branches
- **Untagged jobs** disabled on sensitive runners
- Don't register shell runner on laptop with production secrets

---

## 6. Lab — Day 3

1. Register local Docker runner with tags `handbook`.
2. Update `.gitlab-ci.yml` to require tag `handbook`.
3. Run pipeline; confirm job log shows your runner description.
4. Compare job time on shared vs your runner.

---

## Quick reference

| Task | Command / UI |
|------|----------------|
| Register | `gitlab-runner register` |
| Tags | `tags:` in job |
| Runner UI | Settings → CI/CD → Runners |

**Prev:** [Day 2](../day2/) · **Next:** [Day 4 — Variables & protected branches](../day4/)
