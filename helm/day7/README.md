# Day 7 — Production Charts, CI/CD, GitOps & Security

**Goal:** Design charts for platform teams, wire Helm into CI/CD, align with GitOps (Argo CD / Flux), harden supply chain, and troubleshoot releases under pressure.

**Time:** 6–8 hours (includes capstone)

---

## 1. Chart design principles (professional)

| Principle | Practice |
|-----------|----------|
| **Thin charts** | App chart wraps your image; dependencies for databases |
| **Values as API** | Document every key; avoid breaking renames without MAJOR bump |
| **No secrets in Git** | External Secrets Operator, Sealed Secrets, Vault Agent |
| **Safe defaults** | `runAsNonRoot`, `readOnlyRootFilesystem`, resource requests |
| **Config vs secrets** | ConfigMap for config; Secret for sensitive (or don't template secrets) |
| **One release per app** | Avoid mega-charts unless true system boundary |

**Anti-patterns:**

- Forking upstream chart by copy-paste — use `dependencies` and override values.
- 200-line `--set` in CI — use versioned values files.
- Embedding environment hostnames in templates — use values.

---

## 2. Library charts

`type: library` in `Chart.yaml` — shared `_helpers.tpl` only, not installable alone.

```
charts/
  common-lib/          # type: library
  api/
    Chart.yaml         # depends on common-lib
```

Parent templates:

```yaml
{{- include "common.labels" . | nindent 4 }}
```

Publish library versions like application charts; pin in `dependencies`.

---

## 3. CI/CD pipeline pattern

Typical stages:

```yaml
# .github/workflows/helm.yml (illustrative)
jobs:
  lint:
    steps:
      - run: helm lint charts/api
      - run: helm unittest charts/api -f 'tests/*.yaml'   # optional
  render:
    steps:
      - run: helm template api charts/api -f ci/values.yaml > rendered.yaml
      - run: kubeconform -kubernetes-version 1.29.0 -summary rendered.yaml
  package:
    steps:
      - run: helm dependency build charts/api
      - run: helm package charts/api -d out/
  publish:
    steps:
      - run: helm push out/api-*.tgz oci://${{ env.REGISTRY }}/charts
  deploy-staging:
    steps:
      - run: |
          helm upgrade --install api oci://$REG/charts/api \
            --version ${{ github.ref_name }} \
            -n staging -f deploy/values-staging.yaml \
            --wait --timeout 10m
      - run: helm test api -n staging
```

**Gates:**

- `helm lint` + `helm template` + schema validation on every PR.
- `helm diff` on deploy to prod (manual or automated approval).
- Pin chart version; pin image digest in values for highest assurance.

---

## 4. GitOps with Helm

### Argo CD

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: payments-api
spec:
  project: default
  source:
    repoURL: https://github.com/org/gitops.git
    path: charts/api
    helm:
      valueFiles:
        - values-prod.yaml
      parameters:
        - name: image.tag
          value: "2.4.1"
  destination:
    server: https://kubernetes.default.svc
    namespace: payments
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

Argo renders Helm and applies; cluster drift is reconciled. Helm release history may **not** be used—Argo owns desired state.

### Flux (HelmRelease)

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: api
spec:
  interval: 5m
  chart:
    spec:
      chart: api
      version: "1.2.0"
      sourceRef:
        kind: HelmRepository
        name: internal
  values:
    replicaCount: 3
```

**Helm vs GitOps:** Choose one source of truth per app. Mixing manual `helm upgrade` and Argo selfHeal causes fighting controllers.

---

## 5. Helmfile (multi-release orchestration)

[Helmfile](https://helmfile.readthedocs.io/) declares many releases:

```yaml
repositories:
  - name: bitnami
    url: https://charts.bitnami.com/bitnami

releases:
  - name: redis
    namespace: platform
    chart: bitnami/redis
    version: 20.6.2
    values:
      - redis-values.yaml

  - name: api
    namespace: apps
    chart: ./charts/api
    needs:
      - platform/redis
    values:
      - ./values/api-prod.yaml
```

Useful for platform bootstrap (ingress + cert-manager + monitoring). GitOps often replaces Helmfile for steady-state.

---

## 6. Security and supply chain

| Topic | Action |
|-------|--------|
| RBAC | CI service account: install only in target namespaces |
| Image trust | `image.digest` or admission policies (cosign verify) |
| Chart provenance | Sign with Cosign; verify in CI before deploy |
| Policy | OPA Gatekeeper / Kyverno on rendered manifests |
| Sensitive values | SOPS-encrypted values files decrypted in CI only |

```bash
# Scan chart for misplaced secrets (example tool)
helm template api ./chart | grep -i password || true
```

Never commit `values-prod.yaml` with cleartext DB passwords—use references to ExternalSecret keys.

---

## 7. Observability and operations

Standard labels enable metrics/logs correlation:

```yaml
podLabels:
  app.kubernetes.io/part-of: payments
  app.kubernetes.io/component: api
```

Document runbooks in chart README:

- How to scale (`replicaCount` vs HPA)
- Which values require restart
- Backup/restore for StatefulSet subcharts

---

## 8. Troubleshooting playbook

| Symptom | Checks |
|---------|--------|
| `INSTALLATION FAILED` | `helm status REL -n NS`; hook Jobs `kubectl get jobs` |
| Pending upgrade | Stuck hooks; `helm history`; rollback |
| Wrong image | `helm get values`; compare with Git |
| Service not reachable | `NOTES.txt`; Endpoints; NetworkPolicy |
| Template error | `helm template --debug`; `required` / `fail` messages |

```bash
helm status api -n prod
helm get manifest api -n prod | kubectl apply --dry-run=server -f - 2>&1 | head
kubectl describe deploy -n prod -l app.kubernetes.io/instance=api
kubectl logs -n prod -l app.kubernetes.io/instance=api --tail=100
```

**Debug render without cluster:**

```bash
helm template api ./chart -f values.yaml --debug 2>&1 | less
```

---

## 9. Capstone lab — Day 7

Build a minimal **production-shaped** delivery for `sample-web`:

1. **Repo layout**
   ```
   my-platform/
   ├── charts/sample-web/     # from day2, add probes + resources
   ├── deploy/values-dev.yaml
   ├── deploy/values-prod.yaml
   └── .github/workflows/helm-ci.yaml   # lint + template + kubeconform
   ```

2. **Harden** `values.yaml` defaults: CPU/memory requests, `securityContext` non-root where image allows.

3. **CI** — on PR: `helm lint`, `helm template`, pipe to `kubectl apply --dry-run=client` or kubeconform.

4. **CD** — on tag: `helm package`, push to OCI (or save artifact), `helm upgrade --install --atomic --wait` to `helm-handbook` namespace.

5. **GitOps doc** — write 5 bullets: would Argo or Flux own this app? What happens if someone runs `helm upgrade` manually?

6. **Failure drill** — deploy bad `replicaCount: -1` or invalid image; observe failure; rollback with `helm rollback`.

---

## 10. Certification and next steps

| Resource | Focus |
|----------|-------|
| [Helm docs](https://helm.sh/docs/) | Official reference |
| [Artifact Hub](https://artifacthub.io/) | Discover charts |
| [CNCF CKA](https://www.cncf.io/certification/cka/) | Kubernetes (Helm is adjunct) |
| Kubernetes handbook Day 18+ | Overlaps with cluster-native deploy patterns |

**After Day 7 you should be able to:**

- Author maintainable charts with helpers, hooks, and tests
- Manage dependencies and environment values
- Publish versioned artifacts to HTTP or OCI
- Integrate Helm into CI/CD and explain GitOps tradeoffs
- Debug failed releases methodically

---

## Quick reference

| Area | Tooling |
|------|---------|
| Local render | `helm template` |
| PR validation | `helm lint`, kubeconform, unittest |
| Deploy | `helm upgrade --install --atomic` |
| GitOps | Argo CD Application, Flux HelmRelease |
| Multi-chart | Helmfile or umbrella chart |
| Security | OCI signing, policy admission, External Secrets |

**Previous:** [Day 6](../day6/) · **Handbook home](../README.md)
