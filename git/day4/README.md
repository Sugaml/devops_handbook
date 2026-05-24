# Day 4 — Collaboration: PRs, Stash & Rebase Basics

**Goal:** Work effectively on a team using pull requests, temporary stash, and rebase to keep history clean—the standard workflow in modern DevOps organizations.

**Time:** 6–8 hours

---

## 1. Pull request / merge request workflow

```
Developer                    Remote (GitHub/GitLab)
    │                              │
    ├── push feature branch ──────►│
    ├── open PR/MR ───────────────►│  CI runs tests
    │                              │  Reviewers comment
    ├── push fixes ───────────────►│  CI re-runs
    │                              │
    └── merge (squash/merge/rebase)► main updated
```

| Merge strategy | Result |
|----------------|--------|
| **Merge commit** | Preserves all branch commits + merge commit |
| **Squash merge** | One commit on `main` with combined changes |
| **Rebase merge** | Replays branch commits linearly on `main` (no merge commit) |

**DevOps:** Squash is common for ticket-per-PR teams; rebase merge for strict linear history; merge commit when you want to preserve branch topology.

---

## 2. Typical feature workflow

```bash
# Start from latest main
git switch main
git pull origin main

# Branch per ticket
git switch -c feature/JIRA-456-add-metrics

# Work, commit often with clear messages
echo 'metrics: enabled' >> config.yaml
git add config.yaml
git commit -m "feat(metrics): enable prometheus scraping"

git push -u origin feature/JIRA-456-add-metrics
```

Open PR via web UI or CLI:

```bash
gh pr create --title "feat(metrics): enable prometheus scraping" \
  --body "Closes JIRA-456. Adds scrape config for /metrics endpoint."

# Check CI status
gh pr checks

# After approval, merge (squash example)
gh pr merge --squash --delete-branch
```

Locally after merge:

```bash
git switch main
git pull origin main
git branch -d feature/JIRA-456-add-metrics
```

---

## 3. Review feedback loop

```bash
# More commits on same branch update the PR automatically
git switch feature/JIRA-456-add-metrics
# address review comments
git add .
git commit -m "fix: address review — use standard port name"
git push
```

**Interactive rebase to clean up before merge** (optional, if team allows force-push to feature branch):

```bash
git rebase -i main
# squash fixup commits, reword messages
git push --force-with-lease
```

---

## 4. `git stash` — park work in progress

When you must switch context before committing (production incident, urgent review):

```bash
# Save unstaged + staged changes
git stash push -m "WIP metrics dashboard"

git status    # clean working tree
git switch main
# fix hotfix...

git switch feature/JIRA-456-add-metrics
git stash list
# stash@{0}: On feature: WIP metrics dashboard

git stash pop              # apply latest and remove from stash
# or
git stash apply stash@{0}  # apply but keep in stash
git stash drop stash@{0}
git stash clear            # remove all (careful)
```

**Stash including untracked files:**

```bash
git stash push -u -m "include new files"
```

**Stash specific paths:**

```bash
git stash push -m "only config" -- config.yaml src/
```

**DevOps:** Stash before `git pull --rebase` if you have uncommitted work and can't commit yet.

---

## 5. Rebase fundamentals

Rebase replays your commits on top of another branch—rewrites commit SHAs.

```
Before rebase:
main    ──A──B──C
              \
feature       D──E

After git switch feature && git rebase main:
main    ──A──B──C
                  \
feature           D'──E'   (new SHAs)
```

```bash
git switch main
git pull origin main

git switch feature/my-work
git rebase main

# If conflicts:
# 1. Fix files
# 2. git add resolved-files
# 3. git rebase --continue
# Or abort: git rebase --abort
```

### Golden rule of rebase

**Never rebase commits that have been pushed to a shared branch others use.** Rebasing rewrites history; collaborators' clones diverge.

Safe: rebase local commits or your feature branch before merge (if team allows force-push to feature branches).

---

## 6. Rebase vs merge (team decision)

| Merge | Rebase |
|-------|--------|
| Preserves exact history | Linear, easier `git log` |
| Non-destructive | Rewrites SHAs |
| Merge commits can clutter | No merge commits |
| Safe on shared branches | Shared branches: merge only |

Many teams: **rebase feature onto main locally**, then **squash merge** PR on server.

---

## 7. Syncing a long-lived feature branch

```bash
# Option A: merge main into feature (safe, adds merge commit)
git switch feature/long-running
git merge main

# Option B: rebase feature onto main (linear, rewrites feature commits)
git switch feature/long-running
git rebase main
git push --force-with-lease    # only on YOUR feature branch
```

`--force-with-lease` fails if someone else pushed to the branch since your last fetch—safer than `--force`.

---

## 8. Code review from the CLI

```bash
# GitHub CLI
gh pr list
gh pr view 42
gh pr diff 42
gh pr checkout 42              # checkout PR branch locally

# Review without gh: fetch PR ref
git fetch origin pull/42/head:pr-42
git switch pr-42
git log main..HEAD --oneline
git diff main...HEAD
```

---

## 9. Draft PRs and WIP

```bash
gh pr create --draft --title "WIP: metrics refactor"
# CI may still run; reviewers know it's not ready
gh pr ready 42                 # mark ready for review
```

Use `[WIP]` or `Draft:` prefix in title if your platform supports it.

---

## 10. Handling "your branch is out of date"

GitHub shows "Update branch" — equivalent locally:

```bash
git fetch origin
git switch feature/my-work
git rebase origin/main
# resolve conflicts if any
git push --force-with-lease
```

Or merge:

```bash
git merge origin/main
git push
```

---

## 11. Lab — Day 4

**Setup:** Use your Day 3 repo or create `devops-git-day4` on GitHub.

1. Clone fresh copy. Create `feature/stash-demo`; make uncommitted edits; `git stash`; switch to `main`; pop stash on feature branch.
2. Create `feature/rebase-demo` with 2 commits. On `main`, add 1 commit. Rebase feature onto main; observe new SHAs with `git log --oneline`.
3. Open a PR (draft OK). Push an additional commit; see PR update.
4. Practice `gh pr checkout <num>` or manual fetch of PR ref.
5. Document your team's preferred: merge vs squash vs rebase on PR merge.

**Stretch:** During rebase conflict, use `git rebase --continue` and `git rerere` (if enabled on Day 1) on a second similar conflict.

---

## 12. DevOps connections

- **Required reviewers + CODEOWNERS:** Auto-assign platform team for `terraform/` or `.github/` changes.
- **Status checks:** Branch protection blocks merge until `terraform plan`, `kubectl dry-run`, or unit tests pass.
- **Conventional commits + squash:** One commit per ticket on `main` with message `feat(api): ...` enables automated changelogs.
- **Trunk-based development:** Integrate daily; feature flags hide incomplete work instead of month-long branches.

---

## Quick reference

| Task | Command |
|------|---------|
| Stash WIP | `git stash push -m "msg"` |
| List stashes | `git stash list` |
| Restore stash | `git stash pop` |
| Rebase onto main | `git rebase main` |
| Continue rebase | `git rebase --continue` |
| Abort rebase | `git rebase --abort` |
| Safe force push | `git push --force-with-lease` |
| Open PR (gh) | `gh pr create` |
| Checkout PR | `gh pr checkout 42` |

**Next:** [Day 5 — History: cherry-pick, reset, revert & interactive rebase](../day5/)
