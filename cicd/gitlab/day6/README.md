# Day 6 — Environments, Review Apps & Deployment Jobs

**Goal:** Model staging/production environments, create dynamic review apps for merge requests, and track deployments.

**Time:** 5–6 hours

---

## 1. Environments

```yaml
deploy_staging:
  stage: deploy
  environment:
    name: staging
    url: https://staging.example.com
  script:
    - echo "Deploy $CI_COMMIT_SHORT_SHA"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

deploy_production:
  stage: deploy
  environment:
    name: production
    url: https://example.com
  when: manual
  script:
    - echo "Production deploy"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

Track deployments: **Operate → Environments**.

---

## 2. Review apps (MR previews)

```yaml
review:
  stage: deploy
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: https://$CI_ENVIRONMENT_SLUG.example.com
    on_stop: stop_review
    auto_stop_in: 1 day
  script:
    - echo "Deploy review app for MR $CI_MERGE_REQUEST_IID"
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

stop_review:
  stage: deploy
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop
  when: manual
  script:
    - echo "Stop review environment"
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

Real review apps need K8s/Helm or platform API in `script` — pattern above shows lifecycle hooks.

See [labs/.gitlab-ci.yml](./labs/.gitlab-ci.yml).

---

## 3. Deployment tiers

```yaml
deploy:
  environment:
    name: production
    deployment_tier: production
```

---

## 4. Lab — Day 6

1. Define `staging` and `production` environments with URLs.
2. Add MR-only review job with dynamic environment name.
3. Merge MR; verify staging deploy runs; manually trigger production.
4. View deployment list on Environments page.

---

## Quick reference

| Feature | YAML key |
|---------|----------|
| Environment | `environment.name` |
| Manual prod | `when: manual` |
| Stop review | `action: stop` + `on_stop` |

**Prev:** [Day 5](../day5/) · **Next:** [Day 7 — Production GitLab CI](../day7/)
