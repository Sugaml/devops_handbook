# Day 6 — Reusable Workflows, Composite Actions & Self-Hosted Runners

**Goal:** DRY pipeline logic with reusable workflows, package team actions, run on self-hosted runners, and handle fork PR security.

**Time:** 5–6 hours

---

## 1. Reusable workflow

**`.github/workflows/python-test-reusable.yml`:**

```yaml
on:
  workflow_call:
    inputs:
      python-version:
        required: false
        type: string
        default: '3.12'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ inputs.python-version }}
      - run: pip install -r requirements.txt && pytest -v
```

**Caller:**

```yaml
jobs:
  call-test:
    uses: ./.github/workflows/python-test-reusable.yml
    with:
      python-version: '3.12'
```

See [labs/](./labs/).

---

## 2. Composite action

**`actions/python-test/action.yml`:**

```yaml
name: Python Test
runs:
  using: composite
  steps:
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    - shell: bash
      run: pip install -r requirements.txt && pytest -v
```

Use: `- uses: ./actions/python-test`

---

## 3. Self-hosted runners

Repo → **Settings → Actions → Runners → New self-hosted runner**

```yaml
jobs:
  on-prem-build:
    runs-on: [self-hosted, linux, x64]
    steps:
      - uses: actions/checkout@v4
      - run: make build
```

**Security:** Treat runner VM as production—untrusted fork PRs must not run on shared self-hosted runners without isolation.

---

## 4. Fork PRs and secrets

| Event | Secrets on fork PR |
|-------|-------------------|
| `pull_request` | Not passed (default) |
| `pull_request_target` | **Has secrets — dangerous if checkout PR code** |

**Safe pattern:** Use `pull_request` for untrusted code. Never run untrusted code with `pull_request_target` + default checkout without reading GitHub security advisories.

---

## 5. OIDC to AWS (professional pattern)

```yaml
permissions:
  id-token: write
  contents: read

- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789012:role/github-actions-deploy
    aws-region: us-east-1
```

Configure IAM trust policy for `token.actions.githubusercontent.com`.

---

## 6. Lab — Day 6

1. Extract test job into reusable workflow; call from main CI.
2. Create composite action for setup+test.
3. (Optional) Register self-hosted runner on spare Linux VM.
4. Document fork PR policy for your org.

---

## Quick reference

| Pattern | Trigger |
|---------|---------|
| Reusable | `on: workflow_call` |
| Composite | `runs.using: composite` |
| Self-hosted | `runs-on: [self-hosted, ...]` |

**Prev:** [Day 5](../day5/) · **Next:** [Day 7 — Production GitHub Actions](../day7/)
