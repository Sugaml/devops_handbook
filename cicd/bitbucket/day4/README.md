# Day 4 — Variables, Secured Variables & Deployment Environments

**Goal:** Configure repository and deployment variables, model staging/production environments, and gate releases.

**Time:** 4–6 hours

---

## 1. Repository variables

**Repository settings → Pipelines → Repository variables**

| Type | Behavior |
|------|----------|
| Default | Visible to maintainers in UI |
| **Secured** | Encrypted; not shown after save; masked in logs |

```yaml
- step:
    name: Deploy staging
    script:
      - curl -H "Authorization: Bearer ${STAGING_TOKEN}" https://api.example.com/deploy
```

Add `STAGING_TOKEN` as secured variable in UI.

---

## 2. Deployment environments

**Repository settings → Deployments → Environments**

Create `staging`, `production`. Then in YAML:

```yaml
- step:
    name: Deploy to staging
    deployment: staging
    script:
      - echo "Deploy ${BITBUCKET_COMMIT} to staging"

- step:
    name: Deploy to production
    deployment: production
    trigger: manual
    script:
      - echo "Production deploy"
```

See [labs/bitbucket-pipelines.yml](./labs/bitbucket-pipelines.yml).

**Environment variables** can override per environment in UI.

---

## 3. Deployment permissions

Restrict who can deploy to production:

**Deployments → Environments → production → Restrict deployments**

---

## 4. Bitbucket vs GitHub secrets

| | Bitbucket | GitHub |
|---|-----------|--------|
| Secured vars | Repository + deployment | Secrets + environments |
| Manual prod | `trigger: manual` on step | Environment reviewers |

---

## 5. Lab — Day 4

1. Add secured `STAGING_TOKEN`; verify deploy step sees it (`test -n`).
2. Configure `staging` and `production` deployments.
3. Set production to manual trigger; run pipeline and approve deploy.
4. Restrict production deployment to your user group.

---

## Quick reference

| Item | Location |
|------|----------|
| Secured vars | Pipelines → Repository variables |
| Deploy gate | `deployment:` + `trigger: manual` |
| Env vars | Deployments → Environment → Variables |

**Prev:** [Day 3](../day3/) · **Next:** [Day 5 — Docker & registry push](../day5/)
