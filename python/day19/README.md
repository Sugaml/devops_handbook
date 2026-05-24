# Day 19 — Git Automation with GitPython

**Goal:** Inspect repositories, audit commit history, automate branch operations, and integrate Git metadata into DevOps pipelines using GitPython.

**Time:** 4–5 hours (theory + hands-on)

---

## 1. Why automate Git in DevOps

| Use case | Python + GitPython |
|----------|-------------------|
| CI changelog generation | Commits since last tag |
| Compliance audit | Author email domain checks |
| Release automation | Bump version, commit, tag |
| Repo health reports | Stale branches, unsigned commits |

GitPython wraps the `git` CLI and libgit2 bindings — most operations work on local clones.

```
  CI runner
     │
     ├── git clone (or actions/checkout)
     │
     └── python release_notes.py  ──►  GitPython Repo API
```

---

## 2. Install and open a repository

```bash
pip install gitpython
```

```python
from git import Repo
from pathlib import Path

repo = Repo(Path("/path/to/repo"))
assert not repo.bare

print(repo.working_tree_dir)
print(repo.active_branch.name)
print(repo.head.commit.hexsha[:8], repo.head.commit.summary)
```

**Shallow clones:** Some history operations need depth; CI often uses `fetch-depth: 0` for full history.

---

## 3. Commit history and filtering

```python
def commits_since_tag(repo: Repo, tag: str) -> list:
    tags = [t for t in repo.tags if t.name == tag]
    if not tags:
        raise ValueError(f"tag {tag} not found")
    return list(repo.iter_commits(f"{tag}..HEAD"))

for c in commits_since_tag(repo, "v1.0.0"):
    print(c.hexsha[:8], c.author.email, c.summary)
```

Format release notes:

```python
def format_changelog(commits) -> str:
    lines = []
    for c in commits:
        lines.append(f"- {c.summary} ({c.author.name})")
    return "\n".join(lines)
```

---

## 4. Branches and remotes

```python
# List branches
for branch in repo.branches:
    print(branch.name, branch.commit.hexsha[:8])

# Remote tracking
origin = repo.remote("origin")
print([ref.name for ref in origin.refs])

# Create branch (local)
new_branch = repo.create_head("feature/day19")
new_branch.checkout()
```

Pushing still typically uses `repo.remote().push()` — ensure CI credentials (SSH key or token) are configured.

---

## 5. Diff and changed files

```python
commit = repo.head.commit
parent = commit.parents[0] if commit.parents else None

if parent:
    diff = parent.diff(commit)
    for d in diff:
        print(d.change_type, d.a_path or d.b_path)
```

Use in CI: fail if sensitive paths (`secrets/`, `.env`) appear in diff.

---

## 6. Tags and releases

```python
def create_annotated_tag(repo: Repo, tag_name: str, message: str):
    repo.create_tag(tag_name, message=message)

tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime, reverse=True)
for t in tags[:5]:
    print(t.name, t.commit.hexsha[:8])
```

Prefer annotated tags for releases; lightweight tags for temporary markers.

---

## 7. Safe automation patterns

| Do | Don't |
|----|-------|
| Run in CI on checked-out clone | Commit directly on production servers |
| Use bot account with limited scope | Share personal PAT in scripts |
| Sign commits/tags where policy requires | Force-push `main` from scripts |
| Validate branch name before merge | Auto-merge without checks |

```python
PROTECTED = {"main", "master"}

def assert_not_protected(branch_name: str) -> None:
    if branch_name in PROTECTED:
        raise RuntimeError(f"refusing to modify protected branch {branch_name}")
```

---

## 8. Alternatives: subprocess git

When GitPython lacks a feature, shell out:

```python
import subprocess

result = subprocess.run(
    ["git", "log", "--oneline", "-5"],
    capture_output=True,
    text=True,
    check=True,
    cwd="/path/to/repo",
)
print(result.stdout)
```

Keep a single approach per script for maintainability.

---

## 9. Lab — Day 19

Work from `python/day19/labs/`.

1. `pip install gitpython`.
2. Run `python git_audit.py summary --repo ../../..` (handbook repo root) — branch, last commit, author.
3. Run `python git_audit.py log --repo . --count 10` — recent commits JSON.
4. Run `python git_audit.py stale-branches --repo . --days 90` — branches with no commits in 90 days.
5. Run `python git_audit.py sensitive-diff --repo . --base HEAD~1` — flags if `.env` paths in diff.
6. Initialize a throwaway repo in `/tmp/git-lab`; create commits; run summary again.

**Stretch:** Generate Markdown changelog from commits since the latest tag.

---

## 10. DevOps connections

- **Semantic release:** Tags trigger production deploys — Python validates tag format before push.
- **Policy gates:** Block merge if commit messages lack ticket IDs (`JIRA-123`).
- **Audit:** SOX/HIPAA environments export immutable commit logs from GitPython reports.

---

## Quick reference

| Task | GitPython |
|------|-----------|
| Open repo | `Repo(path)` |
| HEAD commit | `repo.head.commit` |
| Iter commits | `repo.iter_commits("v1..HEAD")` |
| Branches | `repo.branches` |
| Create tag | `repo.create_tag("v1.2.0", message="...")` |
| Diff | `parent.diff(commit)` |

**Next:** [Day 20 — Database health checks](../day20/)
