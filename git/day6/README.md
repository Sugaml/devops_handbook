# Day 6 — Tags, Releases, Signing & Branching Strategies

**Goal:** Mark releases with annotated tags, sign commits for supply-chain trust, and implement branching models used in production DevOps teams.

**Time:** 6–8 hours

---

## 1. Lightweight vs annotated tags

| Type | Stored | Use |
|------|--------|-----|
| **Lightweight** | Pointer to commit | Local bookmarks |
| **Annotated** | Full object: tagger, date, message, optional GPG | **Releases** |

```bash
git tag v1.0.0                     # lightweight
git tag -a v1.0.0 -m "Release 1.0.0: initial production cut"
git tag -a v1.0.1 abc1234 -m "Patch release from specific commit"

git tag                            # list tags
git tag -l "v1.*"                  # pattern
git show v1.0.0                    # tag + commit details

git push origin v1.0.0
git push origin --tags             # push all tags
git push origin :refs/tags/v1.0.0  # delete remote tag (careful)
git tag -d v1.0.0                  # delete local tag
```

**DevOps:** CI triggers on tag push (`on: push: tags: ['v*']`) to build release artifacts, publish to registry, and create GitHub Release.

---

## 2. Checkout tags and release branches

```bash
git switch --detach v1.0.0         # inspect release (detached HEAD)
git switch -c release/1.0-fix v1.0.0   # branch from tag for patches

# Describe current commit relative to nearest tag
git describe --tags
# v1.0.0-5-gabc1234  (5 commits after v1.0.0)

git describe --tags --always --dirty
# used in build metadata: myapp:v1.0.0-5-gabc1234-dirty
```

**Semantic versioning (SemVer):**

```
vMAJOR.MINOR.PATCH
v2.1.0  — new features, backward compatible
v2.1.1  — bugfix only
v3.0.0  — breaking changes
```

Pre-release: `v2.0.0-rc.1`, `v2.0.0-beta.2`

---

## 3. GitHub / GitLab releases

```bash
# GitHub CLI
gh release create v1.0.0 \
  --title "Release 1.0.0" \
  --notes "See CHANGELOG.md" \
  ./dist/app-linux-amd64.tar.gz

gh release list
gh release view v1.0.0
```

Release assets attach binaries, SBOMs, Helm charts—immutable downloads linked to exact Git tag.

---

## 4. Branching strategies

### Trunk-based development

```
main ──●──●──●──●──●──►  (always deployable)
        \    /
         ●──●            short feature branches (< 1 day)
```

- Feature flags hide incomplete work
- CI must be fast and reliable
- Used by Google, many high-performing DevOps teams

### GitFlow (classic)

```
main     ─────●─────────────●──────► releases
               \           /
develop  ──●──●──●──●──●──●──► integration
            \     /
feature      ●──●
```

| Branch | Purpose |
|--------|---------|
| `main` | Production releases only |
| `develop` | Integration branch |
| `feature/*` | New work → merge to develop |
| `release/*` | Stabilize → merge to main + develop |
| `hotfix/*` | Urgent prod fix from main |

**DevOps critique:** GitFlow adds overhead; many cloud-native teams prefer trunk + tags. Still common in enterprise with scheduled releases.

### GitHub Flow (simplified)

```
main ──●──●──●──●──►
        \ /
         ●   feature branch + PR → merge to main → deploy main
```

One long-lived branch; deploy from `main` continuously.

### Environment branches (legacy)

```
dev ──► staging ──► production
```

Often replaced by **GitOps** (single source of truth on `main`, overlays per env) or **promotion pipelines** (same artifact, different config).

---

## 5. Release workflow example

```bash
# 1. Ensure main is green
git switch main
git pull origin main

# 2. Bump version in files (package.json, Chart.yaml, etc.)
echo "2.1.0" > VERSION
git add VERSION
git commit -m "chore(release): bump version to 2.1.0"

# 3. Annotated tag
git tag -a v2.1.0 -m "Release 2.1.0"

# 4. Push
git push origin main
git push origin v2.1.0

# 5. CI builds v2.1.0 artifact; create GitHub Release
gh release create v2.1.0 --generate-notes
```

**Hotfix on release branch:**

```bash
git switch -c hotfix/2.1.1 v2.1.0
# fix bug, commit
git tag -a v2.1.1 -m "Hotfix: security patch"
git push origin hotfix/2.1.1 v2.1.1
# cherry-pick or merge back to main (Day 5)
```

---

## 6. Signed commits and tags (GPG / SSH)

Supply-chain security: prove commits came from you.

### GPG signing

```bash
# Generate key
gpg --full-generate-key

gpg --list-secret-keys --keyid-format=long
# sec   rsa4096/ABC123DEF456  ...

git config --global user.signingkey ABC123DEF456
git config --global commit.gpgsign true
git config --global tag.gpgsign true

git commit -S -m "Signed commit"
git tag -s v1.0.0 -m "Signed release"

# Verify
git log --show-signature -1
git verify-tag v1.0.0
```

Upload public key to GitHub: Settings → SSH and GPG keys.

### SSH commit signing (Git 2.34+)

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
```

**DevOps:** Require signed commits on `main` via branch protection; SLSA and compliance frameworks increasingly expect provenance.

---

## 7. CHANGELOG and conventional commits

Automate release notes from commit messages:

```bash
# Example with git-cliff (install separately)
git cliff --latest --strip header

# Conventional commit format enables tooling
# feat!: breaking API change
# fix(auth): token refresh
# chore(deps): bump lodash
```

Keep `CHANGELOG.md` on `main`; update on release or via CI bot.

---

## 8. Version in artifacts

```bash
VERSION=$(git describe --tags --always --dirty)
docker build -t myapp:${VERSION} .
helm package ./chart --version ${VERSION#v}
```

Traceability: production container `myapp:v2.1.0` ↔ Git tag ↔ exact source tree.

---

## 9. Submodule and subtree (overview)

**Submodule** — pin another repo at specific commit:

```bash
git submodule add git@github.com:org/shared-lib.git libs/shared
git submodule update --init --recursive
# CI must use: git clone --recurse-submodules
```

**Subtree** — merge external repo into subdirectory (simpler for contributors, harder to sync).

Day 7 expands monorepo vs submodule tradeoffs.

---

## 10. Lab — Day 6

1. In a test repo, create 3 commits on `main`. Tag `v0.1.0` annotated; push tag.
2. Add 2 more commits. Run `git describe --tags` and explain output.
3. Branch `release/0.1` from `v0.1.0`; apply hotfix; tag `v0.1.1`.
4. Sketch on paper (or Mermaid) which branching model your ideal team uses and why.
5. If GPG or SSH signing available, sign one commit and verify with `git log --show-signature`.
6. Write a minimal `CHANGELOG.md` entry for `v0.1.1`.

**Stretch:** Configure GitHub Actions `on: push: tags: ['v*']` workflow stub (YAML only) that echoes version.

---

## 11. DevOps connections

- **Immutable releases:** Tags are immutable pointers; never move `v1.0.0` to a different commit—use `v1.0.1`.
- **Helm/K8s:** Chart version often tracks Git tag; Argo CD can sync to `$TAG`.
- **Rollback:** Redeploy previous tag; Kubernetes `helm rollback` + Git tag checkout stay aligned.
- **SBOM & provenance:** Sigstore/cosign signs images; Git signing signs source—layered trust.

---

## Quick reference

| Task | Command |
|------|---------|
| Annotated tag | `git tag -a v1.0.0 -m "msg"` |
| Push tags | `git push origin --tags` |
| Describe commit | `git describe --tags` |
| Branch from tag | `git switch -c branch v1.0.0` |
| Signed commit | `git commit -S -m "msg"` |
| List tags | `git tag -l` |
| GitHub release | `gh release create v1.0.0` |

**Next:** [Day 7 — Hooks, CI/CD, monorepos & production troubleshooting](../day7/)
