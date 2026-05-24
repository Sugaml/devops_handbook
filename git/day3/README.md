# Day 3 — Remotes: Clone, Fetch, Pull & Push

**Goal:** Connect local repos to GitHub/GitLab, sync changes safely, and understand tracking branches—the mechanics behind every CI trigger and team collaboration workflow.

**Time:** 5–7 hours

---

## 1. Local vs remote

```
Your laptop                    GitHub / GitLab (origin)
┌─────────────┐               ┌─────────────────────┐
│  main       │◄── fetch ────►│  origin/main        │
│  feature-x  │─── push ─────►│  feature-x          │
└─────────────┘               └─────────────────────┘
```

| Term | Meaning |
|------|---------|
| **Remote** | Named URL (usually `origin`) pointing to another repo |
| **Remote-tracking branch** | Local read-only pointer like `origin/main` updated by fetch |
| **Upstream** | Branch your local branch tracks (for pull/push defaults) |
| **Fork** | Your copy of someone else's repo; you push to your fork, PR to upstream |

**DevOps:** CI runners `git clone` once, then `git fetch` + checkout. Deploy systems often pull specific tags or SHAs, not floating `main`.

---

## 2. Authentication setup

### HTTPS

```bash
git clone https://github.com/your-org/your-repo.git
# Prompts for credentials; use Personal Access Token (PAT), not account password
```

### SSH (recommended for daily use)

```bash
# Generate key if needed
ssh-keygen -t ed25519 -C "you@example.com" -f ~/.ssh/id_ed25519

# Add public key to GitHub: Settings → SSH keys
cat ~/.ssh/id_ed25519.pub

# Test
ssh -T git@github.com
```

### GitHub CLI (optional)

```bash
brew install gh    # or apt/dnf package
gh auth login
gh repo clone your-org/your-repo
```

---

## 3. Clone a repository

```bash
# HTTPS
git clone https://github.com/your-org/handbook-lab.git
cd handbook-lab

# SSH
git clone git@github.com:your-org/handbook-lab.git

# Specific branch only (shallow single branch — faster for CI)
git clone --branch main --single-branch --depth 1 \
  https://github.com/your-org/handbook-lab.git

# Into specific directory name
git clone git@github.com:your-org/handbook-lab.git my-local-name
```

After clone:

```bash
git remote -v
# origin  git@github.com:your-org/handbook-lab.git (fetch)
# origin  git@github.com:your-org/handbook-lab.git (push)

git branch -vv
# * main abc1234 [origin/main] Latest commit message
```

---

## 4. Remotes management

```bash
# Add remote
git remote add origin git@github.com:your-org/new-repo.git

# Rename
git remote rename origin upstream

# Change URL (e.g. HTTPS → SSH)
git remote set-url origin git@github.com:your-org/repo.git

# Remove
git remote remove old-origin

# Show details
git remote show origin
```

**Fork workflow — two remotes:**

```bash
git remote add upstream git@github.com:original-org/project.git
git fetch upstream
git merge upstream/main    # or rebase (Day 4)
```

---

## 5. Fetch — download without merging

```bash
git fetch origin                    # update all origin/* tracking branches
git fetch origin main               # specific branch
git fetch --all --prune             # all remotes; delete stale tracking refs

# See what changed without merging
git log HEAD..origin/main --oneline
git diff main origin/main
```

**Fetch vs pull:**

| Command | Action |
|---------|--------|
| `git fetch` | Updates `origin/*` only; your branch unchanged |
| `git pull` | `fetch` + merge (or rebase) into current branch |

**DevOps habit:** Run `git fetch --prune` before starting work to see accurate remote state.

---

## 6. Push — upload commits

```bash
# First push: set upstream tracking
git push -u origin feature-login
# equivalent: git push --set-upstream origin feature-login

# Subsequent pushes (upstream configured)
git push

# Push specific branch
git push origin main

# Push all branches
git push --all origin

# Push tags (Day 6)
git push origin v1.0.0
git push origin --tags
```

### Push outcomes

```bash
# Success: remote fast-forwarded
git push origin main

# Rejected: remote has commits you don't (non-fast-forward)
# ! [rejected] main -> main (non-fast-forward)
# Fix: pull first, resolve, then push
git pull origin main
git push origin main
```

**Never force push to shared branches** unless team policy allows (and you understand impact). Day 5 covers `--force-with-lease`.

---

## 7. Pull — fetch + integrate

### Merge pull (default with `pull.rebase false`)

```bash
git switch main
git pull origin main
# fetch + merge origin/main into main
```

### Rebase pull (cleaner linear history)

```bash
git config --global pull.rebase true
git pull origin main
# fetch + rebase local commits on top of origin/main
```

### Explicit control

```bash
git pull --rebase origin main
git pull --no-rebase origin main    # merge even if rebase is global default
```

**Team rule:** Pick merge or rebase for pulls and document it. Mixed habits cause duplicate commits and confusion.

---

## 8. Tracking branches

```bash
# Set upstream for existing branch
git branch -u origin/main
git branch --set-upstream-to=origin/main

# Push and set upstream in one go
git push -u origin feature-x

# Unset upstream
git branch --unset-upstream

# See tracking info
git status -sb
# ## feature-x...origin/feature-x [ahead 2, behind 1]
```

| Status | Meaning |
|--------|---------|
| ahead 2 | 2 local commits not pushed |
| behind 1 | 1 commit on remote not pulled |
| ahead 2, behind 1 | diverged — need pull + merge/rebase before push |

---

## 9. Shallow and partial clones (CI optimization)

```bash
# Shallow clone — no full history (faster, less disk)
git clone --depth 1 git@github.com:org/large-monorepo.git

# Fetch more history later if needed
git fetch --deepen=100
git fetch --unshallow          # full history

# Sparse checkout (monorepo — only one directory)
git clone --filter=blob:none --sparse git@github.com:org/monorepo.git
cd monorepo
git sparse-checkout set services/api
```

**DevOps:** Large repos use shallow clones in CI to cut pipeline time from minutes to seconds.

---

## 10. Mirror and bare repos

```bash
# Bare repo (no working tree — used on servers)
git init --bare /srv/git/myapp.git

# Mirror clone (all refs, for backups or migration)
git clone --mirror git@github.com:org/repo.git
cd repo.git
git push --mirror git@gitlab.com:org/repo.git
```

---

## 11. Lab — Day 3

**Requires:** GitHub/GitLab account and SSH or HTTPS auth configured.

1. Create an empty remote repo named `devops-git-day3` (no README if you want to practice push from scratch).
2. Locally: `mkdir /tmp/devops-git-day3 && cd $_ && git init && echo "# Day 3" > README.md && git add . && git commit -m "Initial commit"`.
3. Add remote: `git remote add origin git@github.com:YOUR_USER/devops-git-day3.git`.
4. Push: `git push -u origin main`.
5. On GitHub web UI, edit README (add a line). Locally: `git fetch && git status` — see behind. `git pull`, then push a local change.
6. Create branch `feature/remote-test`, push with `-u`, verify on remote.
7. Clone into a second directory `/tmp/devops-git-day3-clone` and confirm both copies match.

**Stretch:** Add a second remote pointing to a fork; fetch from both and compare `git remote show`.

---

## 12. DevOps connections

- **Webhook on push:** GitHub sends POST to Jenkins/Argo when you push—remote sync is the CI entry point.
- **Deploy keys:** Read-only SSH keys scoped to one repo for production pull-only servers.
- **Branch environments:** Heroku/Vercel auto-deploy from `main`; GitOps uses commit SHA immutability instead.
- **Rate limits:** CI should cache clones or use shallow fetch; hammering `git clone` full history wastes minutes and API quota.

---

## Quick reference

| Task | Command |
|------|---------|
| Clone | `git clone <url>` |
| List remotes | `git remote -v` |
| Fetch | `git fetch origin` |
| Pull | `git pull origin main` |
| Push | `git push -u origin branch` |
| Set upstream | `git push -u origin branch` |
| Ahead/behind | `git status -sb` |
| Remote details | `git remote show origin` |

**Next:** [Day 4 — Collaboration, PRs, stash & rebase basics](../day4/)
