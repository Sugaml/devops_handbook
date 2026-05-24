# Day 7 — Production GitHub Actions: Security, Governance & Monorepos

**Goal:** Harden Actions for organization scale—pin actions, enforce policies, optimize monorepos, and operate runbooks.

**Time:** 5–7 hours

---

## 1. Production checklist

```
[ ] Pin third-party actions to full SHA (Dependabot/Renovate bumps)
[ ] permissions: block at workflow level — least privilege
[ ] Required reviews + required status checks on main
[ ] Environments with approvers for production
[ ] OIDC to cloud — no long-lived AWS_ACCESS_KEY_ID in secrets
[ ] GITHUB_TOKEN read-only default (org setting)
[ ] Fork PRs cannot access production secrets
[ ] Artifact retention and log archival policy
[ ] Self-hosted runners isolated per trust zone
```

---

## 2. Pin actions to SHA

```yaml
# Instead of @v4 only (lab OK, prod risky)
- uses: actions/checkout@b4ffde65f46336ab88eb137be6937c4b4b8c8a0e # v4.1.1
```

Enable **Dependabot** → `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
```

---

## 3. Organization policies

**Org → Settings → Actions:**

- Allow selected actions (allowlist marketplace + verified creators)
- Require approval for first-time contributor workflows (fork PRs)
- Disable Actions on archived repos

**Rulesets** (Enterprise): require workflows pass before merge org-wide.

---

## 4. Monorepo path filters

```yaml
on:
  push:
    paths:
      - 'services/api/**'
      - '.github/workflows/api-ci.yml'

jobs:
  api-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            api:
              - 'services/api/**'
      - if: steps.filter.outputs.api == 'true'
        run: cd services/api && pytest
```

---

## 5. Cost and performance

- `concurrency` cancel-in-progress on PRs
- Cache pip/npm with lockfile keys
- Split slow E2E to nightly `schedule` workflow
- Use larger runners only when profiled necessary

---

## 6. Troubleshooting

| Issue | Fix |
|-------|-----|
| Workflow not triggering | Check `on:` branches/paths; YAML syntax |
| Permission denied pushing package | Add `packages: write` |
| Secret empty in fork PR | Expected — use `pull_request` + no prod deploy |
| Stuck queued | GitHub-hosted concurrency limits; org billing |
| Action not allowed | Org allowlist |

```bash
gh run view RUN_ID --log-failed
gh workflow list
```

---

## 7. Lab — Day 7 capstone

1. Pin all actions in your CI to SHA; add dependabot config.
2. Set explicit `permissions: contents: read` on all workflows.
3. Add monorepo path filter OR document why full-repo CI is intentional.
4. Write one-page runbook: "CI red on main — what on-call does."

---

## 8. Compare with other tracks

| Topic | GitHub Actions | Jenkins |
|-------|----------------|---------|
| Hosting | GitHub-managed | Self-hosted controller |
| Pipeline file | `.github/workflows/*.yml` | `Jenkinsfile` |
| Secrets | GitHub Secrets + Environments | Credentials plugin |
| Runners | Hosted + self-hosted | Agents |

---

**Prev:** [Day 6](../day6/) · **Track home:** [GitHub README](../README.md)
