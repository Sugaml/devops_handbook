# Day 1 — Bitbucket Pipelines Fundamentals & First Pipeline

**Goal:** Enable Bitbucket Pipelines, understand YAML structure, and run your first build on push.

**Time:** 4–6 hours

---

## 1. Bitbucket Pipelines model

```
bitbucket-pipelines.yml → Bitbucket Cloud → Docker container steps → deploy/artifact
```

| Concept | Bitbucket term |
|---------|----------------|
| Pipeline config | `bitbucket-pipelines.yml` (repo root) |
| Unit of work | **Step** (runs in a container) |
| Group | **Parallel** steps or sequential pipeline |
| Trigger | Default branch, custom, PR, schedule |

Pipelines runs each step in a **Docker image** you specify.

---

## 2. Enable Pipelines

1. Repository → **Repository settings → Pipelines → Settings**
2. Enable Pipelines
3. Add `bitbucket-pipelines.yml` to default branch

---

## 3. Minimal pipeline

```yaml
image: python:3.12-slim

pipelines:
  default:
    - step:
        name: Test
        caches:
          - pip
        script:
          - pip install -r requirements.txt
          - pytest -v
```

See [labs/bitbucket-pipelines.yml](./labs/bitbucket-pipelines.yml).

---

## 4. Branch-specific pipelines

```yaml
pipelines:
  branches:
    main:
      - step:
          name: Test and deploy
          script:
            - pytest -v
            - echo "Deploy from main"
  default:
    - step:
        name: Test only
        script:
          - pytest -v
```

---

## 5. Definitions — caches and services

```yaml
definitions:
  caches:
    pip: ~/.cache/pip

image: python:3.12-slim

pipelines:
  default:
    - step:
        caches:
          - pip
        script:
          - pip install -r requirements.txt && pytest -v
```

---

## 6. Viewing builds

**Pipelines** tab → select run → step log. Bitbucket shows duration and minute usage (plan limits apply).

---

## 7. Lab — Day 1

1. Enable Pipelines on a repo with [sample-web](../../labs/sample-web/).
2. Add [labs/bitbucket-pipelines.yml](./labs/bitbucket-pipelines.yml); push.
3. Confirm green pipeline.
4. Fail a test; confirm red pipeline on commit.

---

## Quick reference

| Item | Value |
|------|--------|
| Config file | `bitbucket-pipelines.yml` |
| Default image | top-level `image:` |
| Minutes | Workspace settings → Plan |

**Next:** [Day 2 — Steps, parallel & services](../day2/)
