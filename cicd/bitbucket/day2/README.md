# Day 2 — Steps, Parallel Builds, Caches & Services

**Goal:** Split work across steps, run jobs in parallel, use caches, and attach Docker-in-Docker services.

**Time:** 4–6 hours

---

## 1. Multiple sequential steps

```yaml
pipelines:
  default:
    - step:
        name: Lint
        script:
          - pip install flake8 && flake8 src/ || true
    - step:
        name: Test
        script:
          - pip install -r requirements.txt && pytest -v
```

Steps in one pipeline entry run **sequentially**; failure stops pipeline.

---

## 2. Parallel steps

```yaml
pipelines:
  default:
    - parallel:
        - step:
            name: Unit tests
            script:
              - pip install -r requirements.txt && pytest -v
        - step:
            name: Lint
            script:
              - pip install flake8 && flake8 src/ || true
```

See [labs/bitbucket-pipelines.yml](./labs/bitbucket-pipelines.yml).

---

## 3. Docker service (build images)

```yaml
definitions:
  services:
    docker:
      memory: 2048

pipelines:
  branches:
    main:
      - step:
          name: Build Docker image
          services:
            - docker
          script:
            - docker build -t myapp:$BITBUCKET_COMMIT .
            - echo "Built ${BITBUCKET_COMMIT}"
```

`docker` service enables `docker` CLI in step (Cloud default memory may need increase for large builds).

---

## 4. Built-in variables

| Variable | Meaning |
|----------|---------|
| `BITBUCKET_COMMIT` | Commit SHA |
| `BITBUCKET_BRANCH` | Branch name |
| `BITBUCKET_BUILD_NUMBER` | Incrementing build id |
| `BITBUCKET_REPO_SLUG` | Repo slug |

---

## 5. Lab — Day 2

1. Split lint and test into parallel steps.
2. Add pip cache in `definitions`.
3. Add Docker build step with `services: [docker]` on `main`.
4. Compare wall time: sequential vs parallel.

---

## Quick reference

| Pattern | YAML |
|---------|------|
| Parallel | `- parallel:` list of steps |
| Cache | `definitions.caches` + `caches:` on step |
| DinD | `services: [docker]` |

**Prev:** [Day 1](../day1/) · **Next:** [Day 3 — Branch & custom pipelines](../day3/)
