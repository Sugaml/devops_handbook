# Day 1 — Git Fundamentals: Install, Config, Commit & Inspect

**Goal:** Understand what Git tracks, configure your environment, and complete the basic edit → stage → commit → inspect loop—the foundation for every DevOps pipeline and GitOps repo.

**Time:** 4–6 hours (theory + hands-on)

---

## 1. Why Git in DevOps?

| Without VCS | With Git |
|-------------|----------|
| "Which version is in prod?" | Tags, branches, and commit SHAs answer exactly |
| Manual file copies on servers | Immutable artifacts built from known commits |
| No audit trail | Every change has author, timestamp, and message |
| Fear of breaking things | Branches and revert give safe experimentation |

**DevOps wins:**

- **CI/CD** triggers on push/merge; pipelines checkout a specific commit SHA.
- **Infrastructure as Code** (Terraform, Ansible, K8s manifests) lives in Git—GitOps controllers reconcile cluster state to repo state.
- **Rollback** = deploy a previous tag or revert a commit, not restore from backup tapes.
- **Blame and bisect** pinpoint when a regression entered production.

Git is distributed: every clone is a full copy of history. You commit locally, then sync with remotes (Day 3).

---

## 2. Install and verify

```bash
# macOS (Homebrew)
brew install git

# Debian/Ubuntu
sudo apt update && sudo apt install -y git

# RHEL/Rocky/Amazon Linux
sudo dnf install -y git

git --version
# git version 2.43.0 or newer is ideal
```

---

## 3. First-time configuration

Git stores config at three levels (later overrides earlier):

| Level | File | Scope |
|-------|------|-------|
| System | `/etc/gitconfig` | All users on machine |
| Global | `~/.gitconfig` | Your user account |
| Local | `.git/config` inside repo | Single repository |

```bash
# Identity — required for meaningful history
git config --global user.name "Alex DevOps"
git config --global user.email "alex@company.com"

# Default branch name for new repos
git config --global init.defaultBranch main

# Where config is read from
git config --list --show-origin | grep user

# Edit global config in your editor
git config --global --edit
```

**Useful global defaults:**

```bash
git config --global color.ui auto
git config --global core.editor "vim"
git config --global init.defaultBranch main
git config --global pull.rebase false          # merge on pull (learn rebase on Day 4+)
git config --global push.autoSetupRemote true  # first push sets upstream (Git 2.37+)
git config --global fetch.prune true           # remove stale remote-tracking branches
git config --global rerere.enabled true        # remember conflict resolutions
```

**DevOps:** CI runners use bot identities (`git config user.email ci@company.com`). Never commit as a personal user from production deploy keys unless policy requires it.

---

## 4. Core concepts

```
Working Directory          Staging Area (Index)         Repository (.git)
     │                            │                            │
  edited files  ──git add──►  staged snapshot  ──git commit──►  permanent record
     │                            │                            │
     └──────── git checkout / restore ◄────────────────────────┘
```

| Term | Meaning |
|------|---------|
| **Repository** | Project folder + hidden `.git` directory (objects, refs, config) |
| **Commit** | Snapshot of staged files + metadata (author, message, parent commit) |
| **SHA-1 hash** | Unique ID like `a1b2c3d4...` (short: first 7–12 chars) |
| **HEAD** | Pointer to current branch/commit |
| **Branch** | Movable pointer to a commit (Day 2) |
| **Remote** | Another copy of the repo (GitHub, GitLab, etc.) — Day 3 |

---

## 5. Create a repository

```bash
mkdir -p /tmp/git-day1 && cd /tmp/git-day1
git init
# Initialized empty Git repository in /tmp/git-day1/.git

ls -la
# .git/ is where all Git metadata lives — do not edit manually unless you know why
```

**Clone vs init:**

```bash
# Start fresh locally
git init my-app && cd my-app

# Copy an existing remote repo (Day 3)
# git clone git@github.com:org/repo.git
```

---

## 6. The basic workflow

### Create and track files

```bash
cd /tmp/git-day1

cat <<'EOF' > README.md
# Git Day 1 Lab
DevOps handbook practice repo.
EOF

cat <<'EOF' > app.sh
#!/usr/bin/env bash
echo "Hello from $(hostname)"
EOF
chmod +x app.sh

git status
# Untracked files: README.md, app.sh
```

### Stage changes (`git add`)

```bash
git add README.md              # stage one file
git add app.sh                 # stage another
git add .                      # stage all changes in current dir (careful in large repos)
git add -p app.sh              # interactive hunk staging (powerful for partial commits)

git status
# Changes to be committed: new file: README.md, new file: app.sh
```

### Commit

```bash
git commit -m "Add README and hello script"

# Multi-line message (subject + body)
git commit -m "Add health check endpoint" -m "Returns 200 OK for load balancer probes."

# Stage tracked modifications and commit in one step (modified files only, not new untracked)
echo "v1" >> README.md
git commit -am "Bump README version note"
```

**Commit message convention (used in many DevOps teams):**

```
type(scope): short summary (50 chars or less)

Optional body explaining why, not what. Link tickets: Fixes #123

Types: feat, fix, docs, chore, refactor, test, ci
```

Example: `fix(ci): retry docker push on transient registry errors`

### View history

```bash
git log
git log --oneline --graph --decorate --all
git log -3                          # last 3 commits
git log --stat                      # files changed per commit
git log -p -1                       # patch for latest commit
git log --author="Alex" --since="2024-01-01"
git show HEAD                       # latest commit details + diff
git show a1b2c3d                    # specific commit (use your SHA)
```

---

## 7. Inspecting changes

### Working tree vs last commit

```bash
echo "# TODO" >> README.md
git status                          # modified: README.md
git diff                            # unstaged changes
git diff README.md

git add README.md
git diff                            # empty (staged)
git diff --staged                   # or --cached: staged vs last commit
```

### Compare commits

```bash
git diff HEAD~1 HEAD                # previous commit vs current
git diff main..feature              # between branches (Day 2)
```

### What changed in a file over time

```bash
git log -p -- README.md            # full history of one file
git blame README.md                 # line-by-line last modifier
git blame -L 1,5 README.md          # lines 1–5 only
```

**DevOps:** During incidents, `git log` + `git blame` on the Terraform module or Helm chart that changed before the outage is standard practice.

---

## 8. Undo and recover (Day 1 level)

| Situation | Command |
|-----------|---------|
| Discard unstaged edits in file | `git restore README.md` |
| Unstage a file | `git restore --staged README.md` |
| Amend last commit message (not pushed yet) | `git commit --amend -m "Better message"` |
| See reflog (safety net) | `git reflog` |

```bash
# Discard all unstaged changes in repo (destructive)
git restore .

# Remove untracked files (preview first)
git clean -n                        # dry run
git clean -fd                       # force remove untracked files/dirs
```

**Rule:** If you already pushed, prefer `git revert` (Day 5) over rewriting history.

---

## 9. `.gitignore`

Prevent secrets, build artifacts, and local IDE files from being committed.

```bash
cat <<'EOF' > .gitignore
# Secrets — NEVER commit
.env
*.pem
credentials.json

# Build output
dist/
build/
*.o

# OS / editor
.DS_Store
.idea/
.vscode/
*.swp

# Dependencies (language-specific)
node_modules/
__pycache__/
.venv/
EOF

git add .gitignore
git commit -m "Add gitignore for secrets and build artifacts"
```

**DevOps:** Leaked `.env` or cloud keys in Git history require rotation *and* history scrubbing (BFG, `git filter-repo`). Prevention beats cleanup.

Global ignore for personal machine noise:

```bash
git config --global core.excludesfile ~/.gitignore_global
echo ".DS_Store" >> ~/.gitignore_global
```

---

## 10. Essential one-liners for Day 1

```bash
git status -sb                      # short branch + status
git diff --name-only                # list changed files
git log --oneline -10
git rev-parse HEAD                  # full SHA of current commit
git rev-parse --short HEAD          # short SHA (used in Docker tags)
git cat-file -t HEAD                # object type (commit)
git ls-files                        # all tracked files
```

---

## 11. Lab — Day 1

1. Create `/tmp/devops-git-day1` and run `git init`.
2. Add `.gitignore` excluding `*.log` and `.env`.
3. Create `deploy.sh` that echoes deployment environment; commit with message `feat(deploy): add deploy script`.
4. Modify `deploy.sh`; use `git diff` before staging. Stage with `git add -p` if you add two changes and only want one in the commit.
5. Run `git log --oneline --graph` and `git show HEAD`.
6. Use `git blame deploy.sh` after a second commit that edits one line—identify which commit touched which line.

**Stretch:** Configure `git config --global alias.st 'status -sb'` and `alias.lg "log --oneline --graph --decorate -20"`. Use them for the rest of the handbook.

---

## 12. DevOps connections

- **Pipeline checkout:** Jenkins/GitHub Actions run `git checkout $SHA` or `actions/checkout@v4`—same object model you use locally.
- **Image tags:** Many teams tag Docker images with `git rev-parse --short HEAD` for traceability.
- **GitOps:** Argo CD and Flux watch a Git repo; every manifest change is a commit—Day 1 skills are the entry point.
- **Audit:** SOC2 and compliance ask "who changed production config?"—Git author + commit metadata answer that.

---

## Quick reference

| Task | Command |
|------|---------|
| New repo | `git init` |
| Status | `git status` |
| Stage | `git add <file>` |
| Commit | `git commit -m "message"` |
| History | `git log --oneline` |
| Unstaged diff | `git diff` |
| Staged diff | `git diff --staged` |
| Discard file edits | `git restore <file>` |
| Ignore patterns | `.gitignore` |

**Next:** [Day 2 — Branches, merge & conflicts](../day2/)
