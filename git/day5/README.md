# Day 5 — Rewriting History: Cherry-pick, Reset, Revert & Interactive Rebase

**Goal:** Move commits between branches, undo mistakes safely, and sculpt history for readable logs—skills every senior DevOps engineer needs for hotfixes, rollbacks, and release maintenance.

**Time:** 6–8 hours

---

## 1. When to rewrite vs preserve history

| Scenario | Tool |
|----------|------|
| Undo pushed commit on shared `main` | `git revert` (safe, new commit) |
| Undo local commit not pushed | `git reset` |
| Apply one fix to another branch | `git cherry-pick` |
| Clean up commits before merge | `git rebase -i` |
| Recover "lost" commit | `git reflog` |

**DevOps rule:** Shared branches (`main`, `production`, release tags) → **revert**, not reset/rebase. Feature branches → rebase/squash OK if team agrees.

---

## 2. `git cherry-pick` — copy a commit

```bash
cd /tmp
rm -rf git-day5 && mkdir git-day5 && cd git-day5
git init

echo "v1" > app.txt && git add . && git commit -m "Initial"
git switch -c develop
echo "feature" >> app.txt && git commit -am "feat: add feature"
FEAT_SHA=$(git rev-parse HEAD)

git switch main
git cherry-pick $FEAT_SHA
# applies same change as new commit on main (different SHA)

# Cherry-pick range
git cherry-pick abc123..def456    # excludes abc123, includes def456

# Cherry-pick without committing (stage only)
git cherry-pick -n $FEAT_SHA      # --no-commit
```

**Conflict during cherry-pick:**

```bash
# fix files
git add .
git cherry-pick --continue
# or skip: git cherry-pick --skip
# or abort: git cherry-pick --abort
```

**DevOps use cases:**

- Hotfix merged to `main` → cherry-pick to `release/2.3` branch
- Port infrastructure fix from `staging` config to `production` branch
- CI replay: build exact commit SHA (not cherry-pick, but same immutability concept)

---

## 3. `git reset` — move branch pointer

```
      A──B──C──D  (HEAD, main)
              ▲
         reset targets
```

| Mode | Working tree | Staging | Use |
|------|--------------|---------|-----|
| `--soft` | unchanged | unchanged | Undo commits, keep changes staged |
| `--mixed` (default) | unchanged | unstaged | Undo commits, keep files edited |
| `--hard` | **discarded** | **discarded** | Nuclear — match commit exactly |

```bash
git reset --soft HEAD~1     # remove last commit, changes stay staged
git reset HEAD~1            # remove last commit, changes unstaged
git reset --hard HEAD~1     # remove last commit AND discard changes
git reset --hard origin/main  # match remote exactly (local work lost)
```

**Unstage file without reset:**

```bash
git restore --staged file.txt
```

---

## 4. `git revert` — safe undo on shared branches

Creates a **new** commit that inverse-applies a previous commit.

```bash
git revert HEAD                    # revert latest commit
git revert abc123                  # revert specific commit
git revert --no-commit abc123      # stage revert without committing yet
git revert -m 1 merge_commit_sha  # revert merge (see below)
```

**Revert a merge commit:**

Merge commits have two parents. `-m 1` means "keep first parent" (usually main line).

```bash
git log --oneline --merges
git revert -m 1 abc1234 -m "Revert release merge due to regression"
git push origin main
```

**DevOps:** Production rollback = deploy previous artifact **or** `git revert` on config repo + GitOps sync. Revert preserves audit trail.

---

## 5. Interactive rebase (`git rebase -i`)

Rewrite last N commits on current branch:

```bash
git rebase -i HEAD~3
```

Editor opens:

```
pick a1b2c3 feat: add endpoint
pick d4e5f6 fix typo
pick g7h8i9 fix typo again

# Commands:
# p, pick = use commit
# r, reword = change message
# e, edit = stop to amend commit
# s, squash = meld into previous commit
# f, fixup = squash discarding message
# d, drop = remove commit
```

After squash/reword:

```bash
git rebase --continue
# or abort: git rebase --abort
```

**Autosquash workflow:**

```bash
git commit --fixup abc123        # creates "fixup! original message"
git rebase -i --autosquash main  # auto-arranges fixup commits
```

---

## 6. `git commit --amend`

Change last commit (message or content)—**only if not pushed to shared branch**.

```bash
git add forgotten-file.txt
git commit --amend --no-edit     # add file to last commit

git commit --amend -m "Better message"
```

If already pushed to personal feature branch:

```bash
git push --force-with-lease
```

---

## 7. Reflog — recovery safety net

Git logs where HEAD and branch tips have been—even "deleted" commits.

```bash
git reflog
# abc1234 HEAD@{0}: commit: latest
# def5678 HEAD@{1}: reset: moving to HEAD~1

git switch -c recovered HEAD@{1}
# or
git reset --hard def5678
```

Reflog expires (default ~90 days); not a backup strategy for long-term recovery.

---

## 8. Finding regressions: `git bisect`

Binary search for the commit that introduced a bug.

```bash
git bisect start
git bisect bad                  # current commit is broken
git bisect good v1.0.0          # known good tag/commit

# Git checks out middle commit — you test and mark:
git bisect good    # or bad
# repeat until culprit found

git bisect reset   # return to original branch
```

**Automated bisect:**

```bash
git bisect start HEAD v1.0.0
git bisect run ./scripts/test.sh
```

**DevOps:** Bisect which Terraform commit broke `plan` or which Docker image tag introduced CVE—pair with CI script that exits 0/1.

---

## 9. Filter and search history

```bash
git log --grep="fix" --oneline
git log -S "password" --oneline       # pickaxe: commits changing string count
git log -G "regex" --oneline
git log --follow -- path/to/file      # through renames
git shortlog -sn                      # commits per author
```

---

## 10. Recovering deleted branches

```bash
git reflog | grep feature-deleted
git switch -c feature-deleted abc1234
```

If commit was garbage-collected (rare locally), recovery may be impossible—another reason remotes matter.

---

## 11. Lab — Day 5

In `/tmp/devops-git-day5`:

1. Create repo with 5 commits on `main`. Use `git reset --soft HEAD~2` and recommit as one—observe history change.
2. Create `release` branch from commit 3. On `main`, add a "hotfix" commit; cherry-pick it onto `release`.
3. On `main`, `git revert` the hotfix; push conceptually—explain why revert beats reset for shared branches.
4. Create messy branch with 4 commits (typos, WIP). `git rebase -i main` squash into 1 clean commit.
5. Run `git bisect` with a script: `test -f fixed.txt` — add `fixed.txt` in commit 3, find it via bisect.
6. `git reset --hard` to wrong place; use `reflog` to recover.

**Stretch:** Revert a merge commit with `-m 1` after creating an intentional merge on a test branch.

---

## 12. DevOps connections

- **Incident rollback:** Revert commit on GitOps repo → controller rolls back K8s manifests automatically.
- **Release branches:** Cherry-pick security patches from `main` to supported releases without full merge.
- **Immutable deploys:** Never "reset" production Git history; tag known-good SHA and redeploy.
- **Compliance:** Auditors prefer revert (visible undo) over force-push (history rewrite).

---

## Quick reference

| Task | Command |
|------|---------|
| Copy commit | `git cherry-pick <sha>` |
| Undo commit (local) | `git reset --soft HEAD~1` |
| Undo commit (shared) | `git revert <sha>` |
| Edit last commits | `git rebase -i HEAD~N` |
| Amend last commit | `git commit --amend` |
| Find bad commit | `git bisect start` |
| Recover lost work | `git reflog` |
| Revert merge | `git revert -m 1 <merge-sha>` |

**Next:** [Day 6 — Tags, releases, signing & branching strategies](../day6/)
