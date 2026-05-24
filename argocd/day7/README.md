# Day 7 — Production GitOps: HA, CI/CD, Observability & Troubleshooting

**Goal:** Harden Argo CD for production — high availability, backup and disaster recovery, Prometheus metrics, notifications, CI/CD integration, secrets management, and a systematic troubleshooting playbook.

**Time:** 6–8 hours

---

## 1. Production architecture

```
                    ┌─────────────────┐
                    │   IdP (OIDC)    │
                    └────────┬────────┘
                             │
┌────────────────────────────▼────────────────────────────┐
│  Ingress (TLS) → argocd-server (2+ replicas)            │
│  argocd-application-controller (sharded at scale)       │
│  argocd-repo-server (2+ replicas, CMP sidecars)         │
│  redis-ha or external Redis                             │
└────────────────────────────┬────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   Cluster: dev        Cluster: staging      Cluster: prod
```

| Concern | Production approach |
|---------|---------------------|
| **Availability** | Multiple replicas, PDB, anti-affinity |
| **Security** | SSO, disable local admin, network policies |
| **Scale** | Controller sharding, repo-server horizontal scale |
| **Secrets** | External Secrets / SOPS / Vault — not plain Git |
| **Observability** | Prometheus metrics, alerts, audit logs |

---

## 2. HA install with Helm

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm upgrade --install argocd argo/argo-cd \
  --namespace argocd \
  --create-namespace \
  -f manifests/helm-values-ha.yaml
```

Key values (see `manifests/helm-values-ha.yaml`):

```yaml
global:
  domain: argocd.example.com

controller:
  replicas: 1          # increase + sharding for 1000+ apps

repoServer:
  replicas: 2
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 5

redis-ha:
  enabled: true

server:
  replicas: 2
  ingress:
    enabled: true
    ingressClassName: nginx
    tls: true

configs:
  params:
    server.insecure: "false"
  cm:
    admin.enabled: "false"
    url: https://argocd.example.com
```

**Controller sharding** (large fleets):

```yaml
controller:
  env:
    - name: ARGOCD_CONTROLLER_REPLICAS
      value: "3"
  sharding:
    enabled: true
    replicas: 3
```

Each shard handles a subset of Applications based on hash.

---

## 3. Backup and disaster recovery

### What to back up

| Asset | Method |
|-------|--------|
| **Git repos** | Source of truth — back up Git hosting (GitHub org backup) |
| **Argo CD CRs** | Export Application, AppProject, ApplicationSet |
| **Secrets** | `argocd-secret`, repo credentials, cluster secrets |
| **argocd-cm / rbac-cm** | ConfigMaps in `argocd` namespace |

Export all Argo CD resources:

```bash
kubectl get applications -n argocd -o yaml > backup/applications.yaml
kubectl get appprojects -n argocd -o yaml > backup/appprojects.yaml
kubectl get applicationsets -n argocd -o yaml > backup/applicationsets.yaml
kubectl get secrets -n argocd -l argocd.argoproj.io/secret-type -o yaml > backup/repo-secrets.yaml
```

Disaster recovery procedure:

1. Recreate cluster (or new management cluster).
2. Reinstall Argo CD (same version if possible).
3. Restore ConfigMaps, secrets, AppProjects.
4. Restore Applications — controller syncs from Git.
5. Re-register external clusters: `argocd cluster add …`

**Critical insight:** If Git is intact, Argo CD state is **recoverable** — Applications are pointers to Git.

Velero / cluster backup can capture `argocd` namespace holistically:

```bash
velero backup create argocd-ns --include-namespaces argocd
```

---

## 4. CI/CD integration patterns

### Pattern A — CI updates Git, Argo CD syncs (recommended)

```
Developer → PR → CI (test, build image) → merge
                → CI commits new image tag to gitops repo
                → Argo CD detects change → sync
```

GitHub Actions example:

```yaml
# .github/workflows/promote.yml
name: Promote image tag
on:
  push:
    branches: [main]
jobs:
  update-gitops:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          repository: myorg/gitops-handbook
          token: ${{ secrets.GITOPS_PAT }}
      - name: Bump image tag
        run: |
          yq -i '.image.tag = "${{ github.sha }}"' apps/api/values-dev.yaml
          git config user.name "ci-bot"
          git config user.email "ci@example.com"
          git commit -am "chore(api): deploy ${{ github.sha }}"
          git push
```

Argo CD auto-sync handles the rest — **CI never touches kubectl**.

### Pattern B — CI triggers sync via API

Use when you need deploy gates after Git update:

```bash
argocd app sync guestbook --grpc-web
# or REST with token
curl -k -H "Authorization: Bearer $ARGOCD_TOKEN" \
  -X POST "https://argocd.example.com/api/v1/applications/guestbook/sync"
```

### Pattern C — Image Updater (optional add-on)

[Argo CD Image Updater](https://argocd-image-updater.readthedocs.io/) watches container registries and writes back to Git — use with caution and pinning policies.

| Pattern | Pros | Cons |
|---------|------|------|
| Git commit from CI | Full audit trail | Extra commit per deploy |
| Manual sync prod | Change control | Slower |
| Image Updater | Automated tag tracking | Can surprise teams |

---

## 5. Secrets management

### External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-db-credentials
  namespace: handbook-lab
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: app-db-credentials
  data:
    - secretKey: password
      remoteRef:
        key: prod/handbook/db
        property: password
```

Git holds `ExternalSecret` YAML; Argo CD syncs it; operator creates the K8s Secret.

### SOPS with age

```bash
age-keygen -o key.txt
sops --encrypt --age $(grep public key.txt) secrets.yaml > secrets.enc.yaml
```

Decrypt via Kustomize plugin or CMP on repo-server — keys mounted from Kubernetes Secret.

**Never:** Commit `stringData` passwords to Git without encryption.

---

## 6. Observability

### Prometheus metrics

Argo CD exposes metrics on:

| Component | Port / path |
|-----------|-------------|
| Application controller | `:8082/metrics` |
| API server | `:8083/metrics` |
| Repo server | `:8084/metrics` |

ServiceMonitor (if Prometheus Operator installed):

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: argocd-metrics
  namespace: argocd
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: argocd-application-controller
  endpoints:
    - port: metrics
```

### Key metrics to alert on

| Metric | Alert when |
|--------|------------|
| `argocd_app_info{sync_status!="Synced"}` | App out of sync > N minutes |
| `argocd_app_info{health_status!="Healthy"}` | App degraded |
| `argocd_app_reconcile_count` errors | Controller reconcile failures |
| `argocd_git_fetch_fail_count` | Repo access broken |

### Notifications

Configure in `argocd-notifications-cm`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
  namespace: argocd
data:
  service.slack: |
    token: $slack-token
  template.app-degraded: |
    message: Application {{.app.metadata.name}} is {{.app.status.health.status}}
  trigger.on-degraded: |
    - when: app.status.health.status == 'Degraded'
      send: [app-degraded]
```

Subscribe Application:

```yaml
metadata:
  annotations:
    notifications.argoproj.io/subscribe.on-degraded.slack: platform-alerts
```

---

## 7. Troubleshooting playbook

### Application stuck OutOfSync

```bash
argocd app get APP --show-operation
argocd app diff APP
argocd app manifests APP --source git   # render errors?
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-repo-server --tail=100
```

Common causes:

| Symptom | Cause | Fix |
|---------|-------|-----|
| Comparison error | Invalid YAML, missing CRD | Fix manifest; sync CRD app first |
| Permission denied | Project RBAC or K8s RBAC | Update AppProject / cluster role |
| Secret drift | Data hash changed | External Secrets or ignoreDifferences |
| Helm template fail | Bad values | `helm template` locally |

### Sync failed / stuck

```bash
argocd app terminate-op APP
argocd app sync APP --force --replace   # last resort
kubectl get events -n DESTINATION_NS --sort-by='.lastTimestamp'
```

### Repo connection failed

```bash
argocd repo get URL
kubectl exec -n argocd deploy/argocd-repo-server -- ls /tmp
# Test clone from repo-server pod
kubectl exec -n argocd deploy/argocd-repo-server -- \
  git ls-remote https://github.com/YOUR_ORG/gitops-handbook.git
```

### High memory on repo-server

- Enable manifest generate cache in `argocd-cm`
- Split monorepo into smaller paths per Application
- Increase repo-server replicas

```yaml
# argocd-cm
data:
  reposerver.parallelism.limit: "10"
  timeout.reconciliation: 180s
```

---

## 8. Security hardening checklist

```
[ ] SSO enabled; admin.enabled: false
[ ] AppProjects restrict repos, destinations, cluster resources
[ ] RBAC default role: readonly
[ ] Repo credentials via Secrets + credential templates
[ ] TLS on argocd-server (ingress or cert-manager)
[ ] NetworkPolicy: limit argocd ↔ kube-api only
[ ] Audit logging enabled (server audit log level)
[ ] Pin Argo CD and Helm chart versions in install
[ ] No cluster-admin for application-controller (custom ClusterRole)
[ ] Secrets via ESO/SOPS — none in plain Git
```

Restrict controller permissions (advanced):

```yaml
# Create dedicated ClusterRole without secrets write to other namespaces
# Helm chart: controller.clusterRoleRules override
```

---

## 9. Promotion workflow — dev to prod

```
gitops-handbook/
├── apps/api/
│   ├── base/
│   └── overlays/
│       ├── dev/      ← auto-sync, branch: main
│       ├── staging/  ← auto-sync, tag: staging-*
│       └── prod/     ← manual sync, tag: v*.*.*
```

| Environment | Revision policy | Sync policy |
|-------------|-----------------|-------------|
| Dev | `main` branch | Automated |
| Staging | Release branch | Automated |
| Prod | Semver tag / SHA | Manual + approval |

Optional: use **Argo CD Sync Waves** across app dependencies (CRDs → operators → apps).

---

## 10. Performance tuning

| Setting | Purpose |
|---------|---------|
| `reposerver.parallelism.limit` | Cap concurrent manifest generation |
| `controller.status.processors` | Reconciliation throughput |
| `controller.operation.processors` | Concurrent sync operations |
| `application.sync.impersonation.enabled` | Sync as dedicated SA per app |

Large monorepo strategies:

1. **Split Applications by path** — one app per microservice directory.
2. **ApplicationSet** — avoid one giant Application.
3. **Manifest generate cache** — reduce repeated Helm/Kustomize runs.

---

## 11. Lab — Day 7

1. Review `manifests/helm-values-ha.yaml` — identify HA-related settings.
2. Export all Applications and AppProjects from your lab cluster to `backup/`.
3. Simulate DR: delete one Application CR; restore from backup YAML; confirm sync.
4. Add a GitHub Actions workflow snippet (on paper or file) that bumps an image tag in Git.
5. Apply `manifests/externalsecret-example.yaml` (requires ESO installed) or document equivalent for your cloud.
6. Port-forward to controller metrics; curl `/metrics` and find `argocd_app_info`.
7. Walk through troubleshooting: intentionally break a manifest in Git, observe sync failure, fix and recover.
8. Complete the **production checklist** (section 8) against your lab install — note gaps.

**Capstone:** Bootstrap a full stack from scratch in 30 minutes:

1. Install Argo CD
2. Apply AppProject + RBAC
3. Apply ApplicationSet for 2 apps
4. Verify sync, metrics, and backup export

---

## 12. DevOps connections

- **SRE:** Argo CD metrics feed the same dashboards as app SLOs — treat the CD plane as production.
- **Change management:** Prod manual sync + Git tag = auditable release record.
- **Platform engineering:** Handbook patterns become internal developer platform docs.

---

## Quick reference

| Task | Command |
|------|---------|
| Export apps | `kubectl get applications -n argocd -o yaml > backup.yaml` |
| Sync via CI | `argocd app sync APP --grpc-web --auth-token $TOKEN` |
| Controller logs | `kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller` |
| Repo server logs | `kubectl logs -n argocd -l app.kubernetes.io/name=argocd-repo-server` |
| Metrics | `kubectl port-forward svc/argocd-metrics -n argocd 8082:8082` |

**Previous:** [Day 6](../day6/)

---

## Where to go next

| Topic | Resource |
|-------|----------|
| Argo Rollouts | Canary/blue-green deployments |
| Crossplane + Argo CD | Infrastructure GitOps |
| Terraform + Argo CD | App-of-apps for Terraform controller |
| Official docs | [argo-cd.readthedocs.io](https://argo-cd.readthedocs.io/) |
| CKA/CKAD + GitOps | Certification + this handbook = strong platform profile |

Congratulations — you have completed the 7-day Argo CD handbook. Your GitOps repo from these labs is portfolio-ready.
