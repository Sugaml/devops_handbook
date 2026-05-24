# Day 1 — GitLab CI Fundamentals & First Pipeline

**Goal:** Understand GitLab CI/CD components, write `.gitlab-ci.yml`, and run your first successful pipeline on GitLab.com or self-managed.

**Time:** 4–6 hours

---

## 1. GitLab CI/CD model

```
.gitlab-ci.yml → GitLab CI/CD → Runner executes jobs → artifacts/registry/environments
```

| Component | Role |
|-----------|------|
| **Pipeline** | Full run for a commit |
| **Stage** | Group of jobs (e.g. test, deploy) |
| **Job** | Script run on a runner |
| **Runner** | Agent that executes jobs (shared SaaS or your own) |
| **Registry** | Built-in container registry per project |

---

## 2. Minimal `.gitlab-ci.yml`

```yaml
stages:
  - test

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

test:
  stage: test
  image: python:3.12-slim
  before_script:
    - pip install -r requirements.txt
  script:
    - pytest -v
```

See [labs/.gitlab-ci.yml](./labs/.gitlab-ci.yml).

---

## 3. Predefined CI variables

| Variable | Meaning |
|----------|---------|
| `CI_COMMIT_SHA` | Full commit hash |
| `CI_COMMIT_SHORT_SHA` | Short hash |
| `CI_COMMIT_BRANCH` | Branch name |
| `CI_PIPELINE_ID` | Pipeline ID |
| `CI_PROJECT_DIR` | Checkout path on runner |

Full list: GitLab docs → Predefined variables.

---

## 4. Enable pipeline

1. Push `.gitlab-ci.yml` to default branch
2. **Build → Pipelines** — first pipeline starts
3. Click pipeline → job → **Browse job log**

**CI/CD lint:** **Build → Pipeline editor → Validate**

---

## 5. When jobs fail

```yaml
test:
  script:
    - pytest -v
  after_script:
    - echo "Job finished with status $CI_JOB_STATUS"
  allow_failure: false   # default — fails pipeline
```

---

## 6. Lab — Day 1

1. Create GitLab project; push [sample-web](../../labs/sample-web/) + `.gitlab-ci.yml`.
2. Confirm green pipeline on `main`.
3. Break test; push; confirm failed pipeline.
4. Use Pipeline Editor to validate YAML before push.

---

## Quick reference

| Task | Location |
|------|----------|
| Config file | `.gitlab-ci.yml` (repo root) |
| Pipelines UI | Build → Pipelines |
| Lint | Pipeline editor → Validate |

**Next:** [Day 2 — Stages, rules & needs](../day2/)
