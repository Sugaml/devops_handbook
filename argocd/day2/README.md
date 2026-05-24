# Day 2 — Applications, Git Sources & Manual Sync

**Goal:** Connect Argo CD to a Git repository, define an `Application` CR, perform manual sync, and operate apps entirely from the CLI.

**Time:** 5–6 hours

---

## 1. The Application custom resource

An **Application** is the central object in Argo CD. It declares:

- **Where** manifests live (`source`)
- **Where** to deploy (`destination`)
- **How** to sync (`syncPolicy`)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: guestbook
  namespace: argocd          # Application CR always lives in argocd ns (or argocd control ns)
spec:
  project: default
  source:
    repoURL: https://github.com/argoproj/argocd-example-apps.git
    targetRevision: HEAD
    path: guestbook
  destination:
    server: https://kubernetes.default.svc
    namespace: handbook-lab
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

Argo CD reads this CR and manages resources **in** `handbook-lab`, not in `argocd`.

---

## 2. Prepare a Git source

### Option A — Upstream example repo (fastest)

```bash
# Public repo — no credentials needed
export REPO_URL=https://github.com/argoproj/argocd-example-apps.git
argocd repo add "$REPO_URL" --type git
argocd repo list
```

### Option B — Your own local bare repo (offline)

```bash
mkdir -p ~/gitops-handbook/apps/guestbook
cp -r labs/guestbook/* ~/gitops-handbook/apps/guestbook/

cd ~/gitops-handbook
git init && git add . && git commit -m "add guestbook app"

# Serve over file:// does NOT work with Argo CD — use a real Git server or push to GitHub
# Quick local server with a bare repo:
git init --bare ~/gitops-handbook.git
cd ~/gitops-handbook
git remote add origin ~/gitops-handbook.git
git push -u origin main

# Port-forward or use file path via Gitea/Forgejo — for labs, GitHub/GitLab is easiest
```

**Production:** Private repos need SSH keys or HTTPS tokens stored as Secrets (Day 5).

Sample app manifests in this handbook:

```
labs/guestbook/
├── deployment.yaml
├── service.yaml
└── kustomization.yaml
```

---

## 3. Create an Application — declarative (GitOps of GitOps)

Bootstrap your first app with a manifest:

```bash
kubectl apply -f manifests/application-guestbook.yaml
```

Or imperative CLI:

```bash
argocd app create guestbook \
  --repo https://github.com/argoproj/argocd-example-apps.git \
  --path guestbook \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace handbook-lab \
  --project default \
  --sync-option CreateNamespace=true
```

Verify:

```bash
argocd app list
argocd app get guestbook
kubectl get application guestbook -n argocd -o yaml
```

---

## 4. Sync workflow

By default, apps are **manual sync** — Argo CD shows OutOfSync but does not apply until you sync.

```bash
# Compare without applying
argocd app diff guestbook

# Sync (apply to cluster)
argocd app sync guestbook

# Watch until healthy
argocd app wait guestbook --health --timeout 120

kubectl get all -n handbook-lab
```

UI equivalent: **App Details → SYNC → Synchronize**.

### Sync phases

1. **Pre-sync** — hooks (Day 3)
2. **Sync** — apply manifests in order (sync waves)
3. **Post-sync** — hooks, notifications
4. **Health assessment** — Deployment replicas, Pod status, custom health

---

## 5. Tracking revisions

```bash
# Sync to specific branch/tag/commit
argocd app set guestbook --revision main
argocd app sync guestbook

# Pin to commit SHA (immutable deploy)
argocd app set guestbook --revision abc1234def
argocd app sync guestbook
```

In the Application CR:

```yaml
source:
  targetRevision: v1.2.0    # tag
  # targetRevision: abc123   # commit
  # targetRevision: HEAD     # default branch tip
```

**Production:** Pin to **commit SHA** or **semver tag** in prod; use branch names only in dev.

---

## 6. Application history and rollback

Each sync creates a **history entry** (like Helm revisions):

```bash
argocd app history guestbook
argocd app rollback guestbook 1   # rollback to history id 1
```

Rollback syncs to the **manifest snapshot** from that deployment, not necessarily an older Git commit — understand the difference:

| Action | Effect |
|--------|--------|
| `git revert` + sync | Git truth moves; cluster follows |
| `argocd app rollback` | Redeploy prior generated manifest set |
| `targetRevision` to old SHA | Git-native rollback |

Prefer **Git revert** for auditability in production.

---

## 7. Delete and finalizers

```bash
# Delete app resources AND the Application CR
argocd app delete guestbook --cascade

# Delete Application CR only (orphan cluster resources)
argocd app delete guestbook --cascade=false
```

If stuck in `Terminating`, check `metadata.finalizers` on the Application.

---

## 8. App-of-Apps pattern (preview)

Manage multiple Applications from one root Application:

```yaml
# bootstrap/root-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: handbook-root
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/YOUR_ORG/gitops-handbook.git
    targetRevision: main
    path: apps
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

The `apps/` folder contains more `Application` YAML files. Day 6 expands this with ApplicationSets.

---

## 9. CLI essentials

```bash
argocd app list -o wide
argocd app get guestbook -o yaml
argocd app resources guestbook          # live objects
argocd app manifests guestbook          # rendered YAML
argocd app logs guestbook               # pod logs (selector-based)
argocd app terminate-op guestbook         # cancel stuck sync
argocd app refresh guestbook            # re-fetch Git
```

---

## 10. Lab — Day 2

1. Add repo `https://github.com/argoproj/argocd-example-apps.git` with `argocd repo add`.
2. Apply `manifests/application-guestbook.yaml` (or use CLI create).
3. Run `argocd app diff guestbook` — review changes before sync.
4. `argocd app sync guestbook` and `argocd app wait guestbook --health`.
5. Confirm Deployment and Service in `handbook-lab` with `kubectl get all -n handbook-lab`.
6. Change `targetRevision` or image tag in Git (fork) or use `helm-guestbook` path; refresh and sync again.
7. View history; practice rollback once.
8. **Stretch:** Create a second Application for `helm-guestbook` path in the same repo.

---

## 11. DevOps connections

- **Promotion flow:** Dev merges → Argo CD auto-syncs dev; prod uses manual sync or protected branch + approval (Day 7).
- **No kubectl in CI:** Pipeline updates image tag in Git; Argo CD is the only deployer.
- **Repository structure:** Separate **app config** (GitOps) from **app source code** repos.

---

## Quick reference

| Task | Command |
|------|---------|
| Create app | `argocd app create NAME --repo URL --path PATH --dest-namespace NS` |
| Diff | `argocd app diff NAME` |
| Sync | `argocd app sync NAME` |
| Wait | `argocd app wait NAME --health` |
| History | `argocd app history NAME` |
| Rollback | `argocd app rollback NAME ID` |

**Previous:** [Day 1](../day1/) · **Next:** [Day 3 — Sync policies & health](../day3/)
