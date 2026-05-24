# Git for DevOps — 7-Day Handbook

A practical, CLI-first path from Git fundamentals to production-grade version control workflows. Each day builds on the previous one with commands, patterns, and labs you can run locally or in CI.

## Structure

| Day | Topic | Folder |
|-----|--------|--------|
| 1 | Install, config, init, commit, diff, log | [day1](./day1/) |
| 2 | Branches, merge, and conflict resolution | [day2](./day2/) |
| 3 | Remotes, clone, fetch, pull, push | [day3](./day3/) |
| 4 | Collaboration, PRs, stash, and rebase basics | [day4](./day4/) |
| 5 | History: rebase, cherry-pick, reset, revert | [day5](./day5/) |
| 6 | Tags, releases, signing, and branching strategies | [day6](./day6/) |
| 7 | Hooks, CI/CD, monorepos, and production troubleshooting | [day7](./day7/) |

## Prerequisites

- Basic Linux/macOS terminal comfort ([Linux handbook](../linux/README.md) Day 1–2 is enough).
- A text editor (`vim`, `nano`, or VS Code).
- A GitHub, GitLab, or Bitbucket account for remote labs (Day 3+).

## How to use this handbook

1. Install Git (Day 1) and configure your identity once.
2. Run every command yourself; use throwaway repos in `/tmp` freely.
3. Complete each day's **Lab** before moving on.
4. Keep a personal cheat sheet of workflows you use at work (merge vs rebase, release tagging, etc.).

## Recommended lab setup

```bash
# Verify Git
git --version

# Minimum useful config (Day 1 covers in depth)
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main
git config --global pull.rebase false   # or true once you understand rebase (Day 4+)

# Optional quality-of-life
git config --global color.ui auto
git config --global core.editor "vim"   # or code --wait, nano, etc.
git config --global fetch.prune true
git config --global rerere.enabled true # reuse recorded conflict resolutions

# Optional tools
# brew install gh git-delta tig   # macOS
# apt install git-delta tig       # Debian/Ubuntu
```

## Design notes

- Examples use `main` as the default branch; replace with your team's convention if needed.
- Placeholder remotes use `git@github.com:your-org/your-repo.git` — swap for your fork.
- DevOps callouts map Git skills to CI/CD pipelines, GitOps, and incident response.
- Labs are self-contained; sample repos are created inline with commands.

## Progress tracker

```
[ ] Day 1  [ ] Day 4  [ ] Day 7
[ ] Day 2  [ ] Day 5
[ ] Day 3  [ ] Day 6
```
