# Day 1 — First GitHub Actions Workflow

**Goal:** Understand GitHub Actions architecture, write your first workflow YAML, and trigger a build on push.

**Time:** 4–6 hours

---

## 1. GitHub Actions in the CI/CD stack

```
git push → GitHub → workflow runner → jobs/steps → artifact/registry
```

| Concept | GitHub term |
|---------|-------------|
| Pipeline definition | Workflow (`.github/workflows/*.yml`) |
| Phase | Job |
| Command | Step |
| Worker | Runner (GitHub-hosted or self-hosted) |
| Trigger | `on:` events |

**Strengths:** Native to GitHub, marketplace actions, OIDC to cloud (Day 6), free minutes for public repos.

---

## 2. Workflow anatomy

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest -v
```

File lives at `.github/workflows/ci.yml` — see [labs/ci.yml](./labs/ci.yml).

---

## 3. Events (`on:`)

| Event | When it fires |
|-------|----------------|
| `push` | Commits pushed to matching branches |
| `pull_request` | PR opened, sync, reopened |
| `workflow_dispatch` | Manual button in Actions tab |
| `schedule` | Cron (`0 6 * * 1` = Mon 06:00 UTC) |
| `release` | Published release |

**Path filters:**

```yaml
on:
  push:
    paths:
      - 'src/**'
      - 'tests/**'
      - '.github/workflows/**'
```

---

## 4. Jobs and steps

- **Jobs** run in parallel by default (unless `needs:`).
- **Steps** in a job run sequentially on the same runner.
- **Default shell:** bash on Linux/macOS, pwsh on Windows.

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "lint placeholder"

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - run: pytest -v
```

---

## 5. Actions vs run

| Type | Syntax | Example |
|------|--------|---------|
| **Action** | `uses: org/action@ref` | `actions/checkout@v4` |
| **Shell** | `run: command` | `run: npm test` |

Pin actions to **commit SHA** in production (Day 7); `@v4` is acceptable in labs.

---

## 6. Permissions (baseline)

```yaml
permissions:
  contents: read
```

Grant minimum scope. Workflows default changed over time—be explicit for new repos.

---

## 7. Viewing runs

- Repo → **Actions** tab → workflow → run
- Expand job → step logs
- Re-run failed jobs or entire workflow

CLI:

```bash
gh run list --workflow=ci.yml
gh run view RUN_ID --log
```

---

## 8. Lab — Day 1

1. Copy [labs/ci.yml](./labs/ci.yml) to your repo's `.github/workflows/ci.yml`.
2. Push to `main`; confirm green run in Actions.
3. Add `workflow_dispatch`; trigger manually.
4. Break a test; push; confirm failed run with red X on commit.

**Stretch:** Add badge to README:

```markdown
![CI](https://github.com/USER/REPO/actions/workflows/ci.yml/badge.svg)
```

---

## 9. DevOps connections

- **Status checks:** Required checks block merge when workflow fails (Day 2 branch protection).
- **Same commit everywhere:** `github.sha` identifies the built artifact.

---

## Quick reference

| Item | Path / key |
|------|------------|
| Workflows | `.github/workflows/*.yml` |
| Checkout | `actions/checkout@v4` |
| Python | `actions/setup-python@v5` |
| Context | `github.sha`, `github.ref`, `github.actor` |

**Next:** [Day 2 — PR workflows & branch protection](../day2/)
