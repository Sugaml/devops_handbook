# Day 4 — Secrets, Environments & Deployment Protection

**Goal:** Store secrets in GitHub, use environments with protection rules, and deploy to staging safely.

**Time:** 4–6 hours

---

## 1. Repository secrets

**Settings → Secrets and variables → Actions → New repository secret**

```yaml
- name: Deploy staging
  env:
    API_TOKEN: ${{ secrets.STAGING_API_TOKEN }}
  run: |
    curl -sf -H "Authorization: Bearer ${API_TOKEN}" \
      "https://api.example.com/deploy?sha=${{ github.sha }}"
```

Secrets are **not** printed in logs (GitHub masks known patterns). Never `echo ${{ secrets.X }}`.

| Scope | Visibility |
|-------|------------|
| Repository secret | All workflows in repo |
| Environment secret | Jobs targeting that environment |
| Organization secret | Selected repos |

---

## 2. Variables (non-secret config)

```yaml
env:
  APP_NAME: ${{ vars.APP_NAME }}
```

**Settings → Secrets and variables → Variables** — plain text, OK for region names, feature flags.

---

## 3. Environments

```yaml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - run: echo "Deploy to staging"
```

Create **staging** and **production** under Settings → Environments.

**Protection rules (production):**

- Required reviewers (1–6 people)
- Wait timer (e.g. 5 minutes)
- Deployment branches: `main` only

---

## 4. Deployment job pattern

See [labs/deploy.yml](./labs/deploy.yml):

```yaml
deploy-staging:
  environment: staging
  steps:
    - run: ./scripts/deploy.sh staging

deploy-production:
  needs: deploy-staging
  environment:
    name: production
  if: github.ref == 'refs/heads/main'
  steps:
    - run: ./scripts/deploy.sh production
```

---

## 5. OIDC preview (full Day 6)

Prefer short-lived cloud tokens over static AWS keys:

```yaml
permissions:
  id-token: write
  contents: read
```

---

## 6. Lab — Day 4

1. Add secret `STAGING_API_TOKEN` (dummy value).
2. Create `staging` environment; add deploy job using secret (curl stub).
3. Create `production` with required reviewer; run workflow; approve deployment.
4. Verify fork PR does not receive production secrets (if testing forks).

---

## Quick reference

| Item | Syntax |
|------|--------|
| Secret | `${{ secrets.NAME }}` |
| Variable | `${{ vars.NAME }}` |
| Environment | `environment: name: staging` |

**Prev:** [Day 3](../day3/) · **Next:** [Day 5 — Docker & GHCR](../day5/)
