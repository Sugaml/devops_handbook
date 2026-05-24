# Day 3 — Sync Policies, Health, Hooks & Drift Control

**Goal:** Configure automated sync (prune, self-heal), use sync options and waves, implement resource hooks, and control drift with `ignoreDifferences`.

**Time:** 5–6 hours

---

## 1. Manual vs automated sync

| Mode | Behavior |
|------|----------|
| **Manual** | Shows OutOfSync; human or CI triggers sync |
| **Automated** | Controller syncs when Git changes or drift detected |

```yaml
spec:
  syncPolicy:
    automated:
      prune: true      # delete cluster resources removed from Git
      selfHeal: true   # revert manual kubectl edits
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - PruneLast=true
```

Enable on existing app:

```bash
argocd app set guestbook --sync-policy automated --self-heal --auto-prune
```

**Production caution:** `prune: true` deletes resources — test in dev first. Use **AppProjects** to limit blast radius (Day 5).

---

## 2. Prune and self-heal in practice

### Self-heal demo

```bash
# With self-heal enabled
kubectl scale deployment guestbook-ui -n handbook-lab --replicas=5
# Within ~3 minutes, controller restores replicas from Git
argocd app get guestbook
```

### Prune demo

Remove a manifest from Git (e.g. delete Service YAML), commit, push:

```bash
argocd app sync guestbook --prune
kubectl get svc -n handbook-lab   # Service gone if removed from Git
```

| Flag | Meaning |
|------|---------|
| `--prune` | Apply deletions during this sync |
| `--dry-run` | Preview sync without apply |
| `--force` | Replace resources when patch fails (use sparingly) |

---

## 3. Sync options reference

Common `syncOptions`:

| Option | Effect |
|--------|--------|
| `CreateNamespace=true` | Create destination namespace if missing |
| `PruneLast=true` | Prune after other resources sync |
| `ApplyOutOfSyncOnly=true` | Skip in-sync resources (faster) |
| `ServerSideApply=true` | Use SSA for large CRDs / field manager conflicts |
| `Replace=true` | Use replace instead of apply (legacy) |
| `SkipDryRunOnMissingResource=true` | Continue if CRD not yet installed |

```yaml
syncPolicy:
  syncOptions:
    - CreateNamespace=true
    - ServerSideApply=true
```

---

## 4. Sync waves and ordering

Resources sync in order: **sync wave** (annotation) → kind order → name.

```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "0"   # earlier
```

Example ordering:

```
Wave -1: Namespace, CRDs
Wave  0: ConfigMaps, Secrets
Wave  1: Deployments
Wave  2: Ingress, HPA
```

```bash
# In Application spec — retry failed syncs
spec:
  syncPolicy:
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

---

## 5. Resource hooks

Hooks run Jobs or Pods at lifecycle points:

| Hook | When |
|------|------|
| `PreSync` | Before apply |
| `Sync` | During apply |
| `PostSync` | After apply, before health check |
| `SyncFail` | After failed sync |
| `PostDelete` | On app deletion |

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: migrate
          image: migrate/migrate:v4.17.0
          command: ["echo", "migration complete"]
```

`hook-delete-policy`: `HookSucceeded`, `HookFailed`, `BeforeHookCreation`.

**DevOps:** Replace `sleep 30` in CI with PostSync hooks that verify readiness.

---

## 6. Health assessment

Argo CD evaluates health per resource type:

| Resource | Healthy when |
|----------|--------------|
| Deployment | Replicas available == desired |
| Service | Exists |
| Ingress | Load balancer assigned (cloud-dependent) |
| CRD / Operator | Custom `lua` health script in `argocd-cm` |

```bash
argocd app get guestbook --show-operation
kubectl get application guestbook -n argocd -o jsonpath='{.status.health.status}'
```

Custom health for CRDs — edit `argocd-cm` ConfigMap:

```yaml
data:
  resource.customizations.health.mycompany.io_MyApp: |
    hs = {}
    if obj.status ~= nil and obj.status.phase == "Running" then
      hs.status = "Healthy"
      hs.message = "Running"
    else
      hs.status = "Progressing"
      hs.message = "Waiting"
    end
    return hs
```

---

## 7. Ignoring differences (drift control)

Some fields are mutated by controllers (HPA, cloud LB annotations, cluster-autoscaler):

```yaml
spec:
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas
    - group: ""
      kind: Service
      jsonPointers:
        - /metadata/annotations/kubectl.kubernetes.io~1last-applied-configuration
```

Or use `jqPathExpressions` for complex cases.

CLI:

```bash
argocd app diff guestbook --local manifests/   # compare local dir to live
```

**Managed fields managers** (SSA):

```yaml
ignoreDifferences:
  - group: apps
    kind: Deployment
    managedFieldsManagers:
      - kube-controller-manager
```

---

## 8. Sync windows (maintenance)

Block or allow syncs on a schedule:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: handbook
  namespace: argocd
spec:
  syncWindows:
    - kind: deny
      schedule: "0 2 * * *"       # 02:00 UTC daily
      duration: 2h
      applications:
        - guestbook
      manualSync: true             # still allow manual override
    - kind: allow
      schedule: "* * * * *"
      duration: 24h
      namespaces:
        - handbook-lab
```

---

## 9. Compare strategies

Application-level diff uses `kubectl diff` semantics. For secrets:

```yaml
syncPolicy:
  syncOptions:
    - RespectIgnoreDifferences=true
```

Refresh intervals:

```yaml
metadata:
  annotations:
    argocd.argoproj.io/refresh: hard   # force full refresh
spec:
  source:
    # ...
```

Controller default refresh: ~3 minutes (`timeout.reconciliation` in argocd-cm).

---

## 10. Lab — Day 3

1. Enable automated sync with prune and self-heal on `guestbook`.
2. Manually scale the Deployment; observe self-heal restore replica count.
3. Apply `manifests/application-with-hooks.yaml` for a PreSync Job; sync and verify hook runs.
4. Add `ignoreDifferences` for `/spec/replicas`; scale manually again — confirm Argo CD ignores drift.
5. Add sync waves: ConfigMap wave 0, Deployment wave 1; verify order in sync operation view.
6. Configure a deny sync window on a test AppProject; attempt sync during window.
7. **Stretch:** Add custom health lua for a simple CRD (or read upstream examples in argo-cd docs).

---

## 11. DevOps connections

- **Git is source of truth** — self-heal enforces that; disable self-heal only for exceptional debugging windows.
- **Prune** prevents orphaned resources when teams remove YAML — essential for cost and security hygiene.
- **Hooks** encode deployment choreography in Git, not tribal CI script knowledge.

---

## Quick reference

| Task | Command |
|------|---------|
| Enable auto-sync | `argocd app set APP --sync-policy automated --self-heal --auto-prune` |
| Sync with prune | `argocd app sync APP --prune` |
| Dry run | `argocd app sync APP --dry-run` |
| Terminate op | `argocd app terminate-op APP` |
| Hard refresh | `argocd app get APP --hard-refresh` |

**Previous:** [Day 2](../day2/) · **Next:** [Day 4 — Helm & Kustomize](../day4/)
