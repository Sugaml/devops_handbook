# Day 3 — Branch Pipelines, Custom Pipelines & Schedules

**Goal:** Control which pipelines run per branch, add manual/custom pipelines, and schedule nightly builds.

**Time:** 4–5 hours

---

## 1. Branch pipelines

```yaml
pipelines:
  branches:
    main:
      - step:
          script:
            - pytest -v && echo "Release path"
    develop:
      - step:
          script:
            - pytest -v
    feature/*:
      - step:
          script:
            - pytest -v --maxfail=1
  default:
    - step:
        script:
          - echo "Other branches"
```

Glob patterns match branch names.

---

## 2. Pull request pipelines

```yaml
pipelines:
  pull-requests:
    '**':
      - step:
          name: PR validation
          script:
            - pip install -r requirements.txt && pytest -v
```

Runs on PR updates; use for required checks before merge.

---

## 3. Custom pipelines (manual)

```yaml
pipelines:
  custom:
    hotfix-deploy:
      - step:
          name: Emergency deploy
          script:
            - echo "Deploy hotfix ${BITBUCKET_COMMIT}"
    full-regression:
      - step:
          size: 2x
          script:
            - pytest -v --runslow
```

Run: **Pipelines → Run pipeline → Custom**

---

## 4. Scheduled pipelines

**Repository settings → Pipelines → Schedules**

- Cron expression (UTC)
- Target branch
- Optional custom pipeline name

Use for nightly security scans, dependency updates.

---

## 5. Lab — Day 3

1. Add `pull-requests` pipeline; open PR and verify build.
2. Add `custom: nightly-test` with larger `size: 2x` (if plan allows).
3. Create weekly schedule on `main`.
4. Push to `feature/x` vs `main`; observe different branch configs.

---

## Quick reference

| Trigger | Key under `pipelines:` |
|---------|------------------------|
| Branch push | `branches:` |
| PR | `pull-requests:` |
| Manual | `custom:` |
| Schedule | UI Schedules |

**Prev:** [Day 2](../day2/) · **Next:** [Day 4 — Variables & deployments](../day4/)
