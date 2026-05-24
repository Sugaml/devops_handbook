# Day 7 — Hooks, CI/CD Integration, Monorepos & Production Troubleshooting

**Goal:** Automate quality gates with Git hooks, wire Git into CI/CD pipelines, navigate monorepos at scale, and debug the Git problems that block releases—the professional DevOps finish line.

**Time:** 7–10 hours

---

## 1. Git hooks overview

Hooks are scripts Git runs at lifecycle events. Live in `.git/hooks/` (not tracked) or via **shared hook path** / **core.hooksPath**.

| Hook | When | Common use |
|------|------|------------|
| `pre-commit` | Before commit recorded | Lint, format, secret scan |
| `commit-msg` | After message entered | Enforce conventional commits |
| `pre-push` | Before push | Run tests, block force-push to main |
| `post-merge` | After merge | `npm install`, submodule update |
| `pre-rebase` | Before rebase | Prevent rebase on protected branches |

```bash
ls .git/hooks/
# sample files end in .sample — rename and chmod +x to activate

# Example: prevent commits to main locally (optional guardrail)
cat <<'EOF' > .git/hooks/pre-commit
#!/usr/bin/env bash
branch=$(git symbolic-ref --short HEAD 2>/dev/null)
if [ "$branch" = "main" ]; then
  echo "Direct commits to main blocked. Use a feature branch."
  exit 1
fi
EOF
chmod +x .git/hooks/pre-commit
```

**Shared hooks for teams:**

```bash
git config core.hooksPath .githooks
mkdir -p .githooks
# commit .githooks/pre-commit to repo — everyone gets same hooks on clone
```

---

## 2. Hook frameworks (production-grade)

Manual bash hooks don't scale; use tools that run fast and only on staged files.

| Tool | Ecosystem |
|------|-----------|
| **pre-commit** (Python) | Language-agnostic hooks marketplace |
| **husky** + **lint-staged** | Node.js projects |
| **lefthook** | Polyglot, fast parallel hooks |

### pre-commit example

```bash
pip install pre-commit   # or brew install pre-commit

cat <<'EOF' > .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: detect-private-key
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
EOF

pre-commit install
pre-commit run --all-files
```

**DevOps:** Hooks catch issues before CI; CI still re-runs everything (defense in depth). Never rely on hooks alone—CI is the enforcement layer.

---

## 3. CI/CD Git integration

### GitHub Actions checkout

```yaml
name: CI
on:
  push:
    branches: [main, 'feature/**']
    tags: ['v*']
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0          # full history for semver/changelog tools

      - name: Git metadata
        run: |
          echo "SHA=$(git rev-parse HEAD)" >> $GITHUB_ENV
          echo "SHORT_SHA=$(git rev-parse --short HEAD)" >> $GITHUB_ENV
          echo "VERSION=$(git describe --tags --always)" >> $GITHUB_ENV

      - run: make test
```

### Jenkins pipeline

```groovy
pipeline {
  agent any
  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh 'git rev-parse HEAD > build/commit.txt'
      }
    }
    stage('Build') {
      steps {
        sh 'docker build -t app:$(git rev-parse --short HEAD) .'
      }
    }
  }
}
```

### GitLab CI

```yaml
variables:
  GIT_DEPTH: "0"    # full clone for describe/bisect

build:
  script:
  - echo "CI_COMMIT_SHA=$CI_COMMIT_SHA"
  - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA .
```

**Key env vars platforms inject:**

| Platform | Commit SHA variable |
|----------|---------------------|
| GitHub Actions | `GITHUB_SHA` |
| GitLab CI | `CI_COMMIT_SHA` |
| Jenkins | `GIT_COMMIT` |

---

## 4. GitOps connection

```
Developer push → Git repo (main)
                      │
                      ▼ webhook / poll
                 Argo CD / Flux
                      │
                      ▼ reconcile
                 Kubernetes cluster
```

Git is the **source of truth**; cluster state drifts are corrected to match repo.

```bash
# Pin deployment to tag (manifest or kustomization)
git log -1 --format=%H v2.1.0
# Argo CD Application spec: targetRevision: v2.1.0
```

**DevOps skills from Days 1–6 directly apply:** branches for env overlays, tags for releases, revert for rollback, signed commits for policy.

---

## 5. Monorepo patterns

Single repo, many services (`google-style` or `nx`/`bazel` shops).

**Challenges:**

- Slow clones → shallow fetch, sparse checkout
- CI runs everything → path-based triggers
- Ownership → CODEOWNERS per directory

```yaml
# GitHub Actions: only test changed paths
on:
  pull_request:
    paths:
      - 'services/api/**'
      - '.github/workflows/api-ci.yml'
```

```bash
# Sparse checkout in CI
git sparse-checkout set services/api packages/shared
```

**Alternatives:**

| Approach | Pros | Cons |
|----------|------|------|
| Monorepo | Atomic cross-service changes | Scale tooling needed |
| Polyrepo + submodule | Clear boundaries | Submodule pain |
| Polyrepo + package registry | Independent release cycles | Cross-repo coordination |

---

## 6. Submodules in CI

```bash
git clone --recurse-submodules git@github.com:org/parent.git
# or after clone:
git submodule update --init --recursive

# Pin submodule to specific commit in parent
cd libs/shared && git checkout abc123 && cd ../..
git add libs/shared
git commit -m "chore: pin shared-lib to abc123"
```

**Failure mode:** CI clones without `--recurse-submodules` → build uses empty directory.

---

## 7. Large repo performance

```bash
# Partial clone (no blob download until needed)
git clone --filter=blob:none git@github.com:org/huge.git

# Shallow for CI
git fetch --depth 1 origin main

# Commit graph optimization (admin)
git commit-graph write --reachable --changed-paths

# Maintenance (Git 2.45+)
git maintenance start
```

**Server-side:** Git LFS for large binaries; don't commit build artifacts or datasets to Git.

---

## 8. Production troubleshooting playbook

### Push rejected (non-fast-forward)

```bash
git fetch origin
git status -sb                    # ahead/behind
git log --oneline HEAD..origin/main
git pull --rebase origin main     # or merge
git push
```

### Merge conflict during pull

```bash
git status                        # unmerged paths
git diff
# resolve markers
git add .
git rebase --continue             # if rebasing
# or git commit                   # if merging
```

### Accidental commit to wrong branch

```bash
git switch wrong-branch
git log -1                        # note SHA
git reset --hard HEAD~1           # remove from wrong branch
git switch correct-branch
git cherry-pick <SHA>
```

### Accidental force push (recovery)

```bash
# On another clone or teammate machine:
git fetch origin
git push origin <good-sha>:main   # restore if permissions allow
# Or contact platform admin / use GitHub reflog for repo (enterprise)
```

### Detached HEAD with commits

```bash
git switch -c save-my-work        # before switching away
```

### Submodule "modified content"

```bash
cd submodule-dir
git status
# commit inside submodule first, then update pointer in parent
```

### `git fsck` — repository integrity

```bash
git fsck --full
# rare corruption; restore from remote clone if needed
```

### Credential / auth failures

```bash
# SSH
ssh -T git@github.com
git remote -v                     # HTTPS vs SSH mismatch

# HTTPS token expired — regenerate PAT
gh auth login
```

---

## 9. Security checklist

- [ ] No secrets in Git history (use `.gitignore`, `detect-private-key` hook, `gitleaks` in CI)
- [ ] Branch protection on `main`: reviews, status checks, no force push
- [ ] Signed commits/tags for release branches (Day 6)
- [ ] Dependabot/Renovate for dependency updates via PR
- [ ] Least privilege deploy keys (read-only where possible)
- [ ] Audit `CODEOWNERS` for infra paths (`terraform/`, `.github/`, `k8s/`)

```bash
# Scan history for secrets (example)
docker run -v $(pwd):/repo zricethezav/gitleaks detect -s /repo --no-git
# or: gitleaks detect --source . --log-opts -1
```

If secret leaked: **rotate credential**, then remove from history with `git filter-repo` or BFG (team coordination required).

---

## 10. Useful aliases and config (professional kit)

```bash
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st 'status -sb'
git config --global alias.lg "log --oneline --graph --decorate -20"
git config --global alias.last 'log -1 HEAD --stat'
git config --global alias.unstage 'restore --staged'
git config --global alias.undo 'reset --soft HEAD~1'

# Better diffs with delta (install delta separately)
git config --global core.pager 'delta'
git config --global interactive.diffFilter 'delta --color-only'
```

```bash
# ~/.gitconfig excerpt
[merge]
  conflictstyle = diff3
[pull]
  rebase = false
[fetch]
  prune = true
[rerere]
  enabled = true
[init]
  defaultBranch = main
```

---

## 11. Capstone lab — Day 7

Build a mini **DevOps Git workflow** end to end:

1. **Repo setup:** Create `devops-git-capstone` with `.pre-commit-config.yaml` (or simple `.githooks/pre-commit` secret scan).
2. **App:** Add `app/` with a Dockerfile; version in `VERSION` file.
3. **CI stub:** Add `.github/workflows/ci.yml` that checks out repo, prints `git describe --tags --always`, runs a dummy test.
4. **Branch flow:** Feature branch → PR → squash merge to `main`.
5. **Release:** Tag `v1.0.0`; extend workflow with `on: push: tags`.
6. **Hotfix:** Branch from tag, fix, tag `v1.0.1`, cherry-pick to `main`.
7. **Rollback drill:** `git revert` a bad commit on `main`; document rollback runbook in `RUNBOOK.md`.
8. **Break/fix:** Intentionally cause non-fast-forward push; recover using fetch + rebase.

**Deliverables:** Working repo, 2 tags, CI YAML, RUNBOOK.md with 5 troubleshooting steps you practiced.

---

## 12. What "professional" looks like

| Junior | Professional |
|--------|--------------|
| `git add .` always | Staged, focused commits; `git add -p` |
| Merge conflicts panic | Calm diff3 resolution; rerere enabled |
| Force push to fix | `--force-with-lease`; policy-aware |
| "It works on my machine" | SHA tagged artifacts match Git |
| Ignores hooks | pre-commit + CI parity |
| Single remote | Fork/upstream, fetch --prune habit |

---

## 13. Further learning

- **Pro Git** (free book): https://git-scm.com/book
- **GitHub Docs:** branch protection, rulesets, merge queues
- **Atlassian Git tutorials:** advanced merging and workflows
- **Software Supply Chain:** Sigstore, SLSA, in-toto attestations
- **Adjacent handbook topics:** [Docker CI/CD](../docker/day7/), [Kubernetes GitOps](../kubernetes/day23/)

---

## Quick reference

| Task | Command |
|------|---------|
| Install shared hooks | `git config core.hooksPath .githooks` |
| CI full history | `fetch-depth: 0` / `GIT_DEPTH: "0"` |
| Submodule clone | `git clone --recurse-submodules` |
| Sparse checkout | `git sparse-checkout set path/` |
| Repo integrity | `git fsck` |
| Secret scan | `gitleaks detect` |
| Build version | `git describe --tags --always` |

---

## Handbook complete

You now have a path from `git init` to production GitOps, releases, and incident recovery. Revisit days as needed at work—**Day 3–5** repay daily practice most often.

**Related:** [Linux handbook](../linux/README.md) · [Docker handbook](../docker/README.md) · [Kubernetes handbook](../kubernetes/README.md)
