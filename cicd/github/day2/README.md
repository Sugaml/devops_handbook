# Day 2 — Jobs, PR Workflows & Branch Protection

**Goal:** Run CI on pull requests, enforce required status checks, and structure multi-job workflows with `needs`.

**Time:** 4–6 hours

---

## 1. PR vs push triggers

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
    branches: [main]
```

| Context | `github.event_name` | Notes |
|---------|---------------------|-------|
| PR from same repo | `pull_request` | Full secrets per policy |
| Push to main | `push` | Deploy stages often here |
| Fork PR | `pull_request` | **Restricted secrets** (Day 6) |

**Checkout PR head:**

```yaml
- uses: actions/checkout@v4
  with:
    ref: ${{ github.event.pull_request.head.sha }}
```

Default checkout on `pull_request` is merge commit—usually what you want for "will main break?".

---

## 2. Multi-job pipeline

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install flake8 && flake8 src/

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt && pytest -v
```

See [labs/ci-pr.yml](./labs/ci-pr.yml).

---

## 3. Branch protection

Repo → **Settings → Branches → Add rule** for `main`:

- [x] Require a pull request before merging
- [x] Require status checks to pass (`test`, `lint`)
- [x] Require branches to be up to date (optional)

Failed CI blocks merge when checks are required.

---

## 4. Job outputs

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.meta.outputs.version }}
    steps:
      - id: meta
        run: echo "version=1.0.${GITHUB_RUN_NUMBER}" >> "$GITHUB_OUTPUT"

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploy ${{ needs.test.outputs.version }}"
```

---

## 5. Concurrency (cancel outdated PR builds)

```yaml
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```

Saves minutes when pushing frequently to a PR branch.

---

## 6. Lab — Day 2

1. Split workflow into `lint` + `test` jobs with `needs`.
2. Open PR; verify both jobs run and appear on PR checks.
3. Enable branch protection requiring `test` and `lint`.
4. Push failing commit to PR — merge button blocked.

---

## Quick reference

| Task | YAML |
|------|------|
| Job dependency | `needs: other-job` |
| PR only | `on: pull_request` |
| Outputs | `echo "k=v" >> $GITHUB_OUTPUT` |

**Prev:** [Day 1](../day1/) · **Next:** [Day 3 — Matrix & cache](../day3/)
