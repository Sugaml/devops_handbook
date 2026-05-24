# Day 4 — CI/CD Variables, Protected Branches & Masked Secrets

**Goal:** Manage project/group variables, protect production configuration, and integrate external secret stores.

**Time:** 4–6 hours

---

## 1. Variable scopes

**Settings → CI/CD → Variables**

| Flag | Effect |
|------|--------|
| **Protected** | Only on protected branches/tags |
| **Masked** | Hidden in logs (regex constraints) |
| **Expanded** | `$VAR` not expanded in value |

```yaml
deploy:
  script:
    - curl -H "PRIVATE-TOKEN: ${STAGING_TOKEN}" https://api.example.com/deploy
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

Define `STAGING_TOKEN` in UI — never in `.gitlab-ci.yml`.

---

## 2. `.gitlab-ci.yml` variables

```yaml
variables:
  APP_ENV: staging
  DOCKER_DRIVER: overlay2

deploy:
  variables:
    APP_ENV: production
  script:
    - echo "Deploy to $APP_ENV"
```

**Environment-scoped variables:** Settings → CI/CD → Variables → Environment scope `production`.

---

## 3. Protected branches

**Settings → Repository → Protected branches**

- `main`: Maintainers can merge; Developers can push via MR only
- **Allowed to deploy** roles for manual jobs

```yaml
deploy_production:
  when: manual
  environment: production
  only:
    - main
  # prefer rules: in new configs
```

---

## 4. File-type variables

Store kubeconfig or JSON key as **File** variable — GitLab writes to temp path:

```yaml
deploy:
  script:
    - kubectl --kubeconfig "$KUBECONFIG" apply -f manifest.yaml
```

Variable `KUBECONFIG` type File → path injected.

---

## 5. Vault integration (overview)

GitLab Premium/Ultimate: native HashiCorp Vault secrets in CI. Self-managed: fetch via API in `before_script` with JWT (`CI_JOB_JWT` / ID tokens).

---

## 6. Lab — Day 4

1. Add masked variable `STAGING_TOKEN`; use in deploy script (test `-n "$STAGING_TOKEN"`).
2. Protect `main`; require MR to merge.
3. Mark variable **protected**; run job on feature branch — variable absent (expected).
4. Add environment-scoped variable for `production`.

---

## Quick reference

| Item | Location |
|------|----------|
| Project variables | Settings → CI/CD → Variables |
| Protected branches | Settings → Repository |
| Masked | Must be single-line, sufficient entropy |

**Prev:** [Day 3](../day3/) · **Next:** [Day 5 — Docker & registry](../day5/)
