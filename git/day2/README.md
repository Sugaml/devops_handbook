# Day 2 — Branches, Merge & Conflict Resolution

**Goal:** Work on isolated branches, merge changes safely, and resolve conflicts—the daily workflow behind feature development, hotfixes, and release branches.

**Time:** 5–7 hours

---

## 1. Why branches matter in DevOps

```
main ─────●─────●─────●─────●─────►  (production-ready)
           \         /
feature ────●───●───●                 (developer work)
             \
hotfix ───────●───●                   (urgent prod fix)
```

| Pattern | Branch use |
|---------|------------|
| Trunk-based | Short-lived branches; merge to `main` several times/day |
| GitFlow | `develop`, `release/*`, `hotfix/*` (Day 6) |
| Environment branches | `staging`, `production` (GitOps often replaces this) |
| PR/MR workflow | Branch per ticket; CI runs on branch before merge |

**DevOps:** CI pipelines typically run on every push to a branch. Protected `main` requires passing checks + review before merge.

---

## 2. Branch basics

```bash
cd /tmp
rm -rf git-day2 && mkdir git-day2 && cd git-day2
git init

echo "base" > app.txt
git add app.txt && git commit -m "Initial commit"

# List branches (* = current)
git branch
# * main

# Create branch (does not switch)
git branch feature-login

# Switch branch (modern)
git switch feature-login
# or legacy: git checkout feature-login

# Create and switch in one command
git switch -c feature-metrics

# See all branches with last commit
git branch -v
git branch -a                    # include remotes (after Day 3)
```

**Naming conventions (teams vary):**

```
feature/JIRA-123-add-oauth
fix/null-pointer-api
hotfix/prod-db-connection
release/2.4.0
chore/update-terraform-provider
```

---

## 3. Work on a branch and merge

```bash
git switch main
git switch -c feature-greeting

echo "Hello, DevOps" >> app.txt
git add app.txt
git commit -m "feat: add greeting line"

# Switch back to main and merge
git switch main
git merge feature-greeting
```

### Fast-forward merge

When `main` has no new commits since the branch diverged, Git moves the pointer forward—no merge commit.

```
Before:  main ──A
              \
         feature ──B

After:   main ──A──B   (feature pointer still at B)
```

```bash
git log --oneline --graph --decorate
# Linear history — often preferred for trunk-based teams
```

### Three-way merge (merge commit)

When both branches advanced, Git creates a merge commit with two parents.

```bash
git switch main
echo "main update" >> app.txt && git commit -am "chore: update main"

git switch -c feature-api
echo "api v1" >> api.txt && git add api.txt && git commit -m "feat: add api file"

git switch main
git merge feature-api
# Merge made by the 'ort' strategy (or recursive in older Git)
```

```bash
git log --oneline --graph --decorate
# Shows merge commit with two parents
```

**Merge options:**

```bash
git merge feature-api --no-ff          # always create merge commit
git merge feature-api --ff-only        # fail if fast-forward not possible
git merge feature-api -m "Merge feature-api into main"
git merge --abort                      # cancel conflicted merge
```

---

## 4. Delete and cleanup branches

```bash
# Delete merged branch
git branch -d feature-greeting

# Force delete unmerged branch
git branch -D feature-old

# Delete remote branch (Day 3)
# git push origin --delete feature-old
```

---

## 5. Merge conflicts

Conflicts occur when the same lines were changed differently on both branches.

### Reproduce a conflict

```bash
cd /tmp
rm -rf git-conflict-lab && mkdir git-conflict-lab && cd git-conflict-lab
git init

cat <<'EOF' > config.yaml
port: 8080
host: localhost
EOF
git add config.yaml && git commit -m "Add config"

git switch -c branch-a
sed -i '' 's/port: 8080/port: 9090/' config.yaml 2>/dev/null || \
  sed -i 's/port: 8080/port: 9090/' config.yaml
git commit -am "branch-a: change port to 9090"

git switch main
git switch -c branch-b
sed -i '' 's/port: 8080/port: 3000/' config.yaml 2>/dev/null || \
  sed -i 's/port: 8080/port: 3000/' config.yaml
git commit -am "branch-b: change port to 3000"

git switch main
git merge branch-a    # succeeds
git merge branch-b    # CONFLICT
```

### Conflict markers in file

```
<<<<<<< HEAD
port: 9090
=======
port: 3000
>>>>>>> branch-b
```

### Resolve manually

```bash
git status
# both modified: config.yaml

# Edit file — pick one value or combine:
# port: 9090

git add config.yaml
git commit -m "Merge branch-b; keep port 9090"
# or if merge was in progress: git commit (default merge message)
```

### Tools for conflict resolution

```bash
git mergetool                  # opens configured tool (vimdiff, meld, vscode)
git diff                       # shows conflict state
git checkout --ours config.yaml    # keep current branch version
git checkout --theirs config.yaml  # keep incoming branch version
git merge --abort              # start over
```

**DevOps:** Terraform state conflicts and Helm value merges in GitOps repos follow the same marker pattern—resolve, test, commit.

---

## 6. Compare branches

```bash
git log main..feature-api          # commits on feature not in main
git log feature-api..main          # commits on main not in feature
git log --left-right main...feature-api   # symmetric difference

git diff main..feature-api         # diff of file contents
git diff main...feature-api        # diff since common ancestor (three-dot)
```

**Three-dot diff** is what GitHub shows in PRs: changes introduced on the feature branch since it diverged.

---

## 7. Detached HEAD (know this)

Checking out a commit SHA directly puts you in detached HEAD—you're not on a branch.

```bash
git switch main
COMMIT=$(git rev-parse HEAD~1)
git switch --detach $COMMIT
# HEAD detached at abc1234

# Commits here are reachable via reflog but easy to lose
git switch main                  # return safely
```

Use detached HEAD for inspecting old releases; create a branch if you need to commit: `git switch -c fix-from-old-release`.

---

## 8. Branch protection concepts (remote)

On GitHub/GitLab (configured in UI, not Git CLI):

- Require pull request before merge to `main`
- Require status checks (CI green)
- Require code review
- Block force push
- Require signed commits (Day 6)

Local Git has no "protection"—discipline + server rules enforce quality.

---

## 9. Lab — Day 2

1. In `/tmp/devops-git-day2`, init repo with `README.md` on `main`.
2. Create `feature/ci` branch; add `.github/workflows/ci.yml` placeholder (even empty YAML); commit.
3. On `main`, add a line to `README.md`; commit.
4. Merge `feature/ci` into `main`—observe merge commit vs fast-forward depending on order.
5. Create two branches that both edit the same line in `README.md`; merge both into `main` and resolve conflict intentionally.
6. Run `git log --oneline --graph --all` and explain the graph in your notes.

**Stretch:** Configure `git config merge.conflictstyle diff3` for richer conflict markers showing the common ancestor.

---

## 10. DevOps connections

- **Feature flags vs long branches:** Trunk-based DevOps favors small branches merged daily; long-lived branches drift and cause painful merges.
- **CI on branch:** `on: push: branches: ['**']` in GitHub Actions runs tests per branch—broken merges caught before `main`.
- **Release branches:** Some teams cut `release/1.2` from `main`, cherry-pick fixes, then merge back (Day 5–6).

---

## Quick reference

| Task | Command |
|------|---------|
| List branches | `git branch -v` |
| Create + switch | `git switch -c name` |
| Switch | `git switch name` |
| Merge | `git merge branch` |
| Abort merge | `git merge --abort` |
| Delete merged branch | `git branch -d name` |
| Commits not in main | `git log main..feature` |
| PR-style diff | `git diff main...feature` |

**Next:** [Day 3 — Remotes, clone, fetch, pull, push](../day3/)
