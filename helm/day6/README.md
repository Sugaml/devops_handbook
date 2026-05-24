# Day 6 — Package, Publish, OCI, Rollback & Tooling

**Goal:** Version and package charts, host them on HTTP or OCI registries, integrate diff/validation plugins, and operate upgrades/rollbacks like production.

**Time:** 5–7 hours

---

## 1. SemVer for charts

| Change | Bump |
|--------|------|
| Breaking template or values contract | **MAJOR** |
| New features, backward compatible | **MINOR** |
| Bugfix, docs only | **PATCH** |

`Chart.yaml` `version` is chart SemVer; `appVersion` is informational unless templates reference it.

```bash
# After editing Chart.yaml version
helm package ./labs/sample-web -d /tmp/charts
ls -la /tmp/charts/sample-web-0.1.0.tgz
```

---

## 2. `helm package` and install from tarball

```bash
helm package /Users/babulaltamang/Documents/devops_handbook/helm/day2/labs/sample-web -d /tmp/pkg

helm install from-tgz /tmp/pkg/sample-web-0.1.0.tgz -n helm-handbook
```

Package includes `templates/`, `values.yaml`, `Chart.yaml`, and `charts/*.tgz` dependencies—run `helm dependency build` first.

---

## 3. HTTP chart repository (classic)

```bash
# Generate index from packaged charts
helm repo index /tmp/pkg --url https://charts.example.com/releases

# index.yaml lists chart name, version, digest, URLs
cat /tmp/pkg/index.yaml
```

Host `index.yaml` + `.tgz` files on static HTTP (S3, GCS, nginx) or ChartMuseum:

```bash
# ChartMuseum (lab)
docker run -d -p 8080:8080 \
  -e STORAGE=local \
  -e STORAGE_LOCAL_ROOTDIR=/charts \
  -v /tmp/pkg:/charts \
  ghcr.io/helm/chartmuseum:v3.10.0

curl -X POST --data-binary "@/tmp/pkg/sample-web-0.1.0.tgz" http://localhost:8080/api/charts

helm repo add local http://localhost:8080
helm search repo local
```

---

## 4. OCI registries (modern default)

Helm 3.8+ pushes/pulls charts as OCI artifacts:

```bash
# Login (example: GHCR)
helm registry login ghcr.io -u USER

helm package ./day2/labs/sample-web -d /tmp/pkg

helm push /tmp/pkg/sample-web-0.1.0.tgz oci://ghcr.io/YOUR_ORG/charts

helm install web oci://ghcr.io/YOUR_ORG/charts/sample-web --version 0.1.0 -n helm-handbook
```

| Registry | Notes |
|----------|-------|
| GHCR / Harbor / ECR | Enable OCI; reuse image registry credentials |
| Artifact Hub | Discovery; not a private host |

**Production:** Sign charts (Cosign), scan artifacts, immutability tags per version.

---

## 5. Upgrade strategies

```bash
helm upgrade --install api ./chart -n prod -f values-prod.yaml --wait --timeout 15m

# Atomic — rollback on failure
helm upgrade api ./chart -n prod --atomic --wait

# Force pod restart when only config changed
helm upgrade api ./chart -n prod --recreate-pods   # deprecated pattern; prefer checksum annotation on deployment
```

**Checksum pattern** (roll pods when ConfigMap changes):

```yaml
metadata:
  annotations:
    checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

---

## 6. History, rollback, and recovery

```bash
helm history api -n prod
helm rollback api 3 -n prod
helm rollback api -n prod   # rolls back one revision
```

| Scenario | Action |
|----------|--------|
| Bad values in upgrade | `helm rollback` or re-run upgrade with good `-f` |
| Stuck pending | `helm history`; check hook Jobs; may need `helm rollback` |
| Secret release storage full | Archive old releases (`helm max-history` in chart or `--history-max`) |

```bash
helm install api ./chart -n prod --history-max 10
```

---

## 7. Plugins

### helm-diff

```bash
helm plugin install https://github.com/databus23/helm-diff

helm diff upgrade api ./chart -n prod -f values-prod.yaml
```

Use in CI: fail if unexpected resources change.

### kubeconform / helm unittest

- **kubeconform** — validate rendered YAML against JSON schemas.
- **helm unittest** — unit test templates with expected snippets.

```bash
helm template api ./chart -f values-prod.yaml | kubeconform -summary -
```

---

## 8. Release secrets and metadata

```bash
kubectl get secrets -n helm-handbook -l owner=helm
helm get metadata api -n helm-handbook
```

Default storage is `secret`; alternative drivers exist for advanced multi-cluster patterns.

---

## 9. Lab — Day 6

1. Package [day2 sample-web](../day2/labs/sample-web/); verify `.tgz` contents: `tar tzf sample-web-0.1.0.tgz`.
2. Generate `helm repo index` for `/tmp/pkg`; inspect `index.yaml` digest field.
3. (Optional) Push to a local registry with `registry:2` + `helm push` if you run Docker.
4. Install `helm-diff`; run `helm diff upgrade` before a replica change.
5. Install a release, perform two upgrades, `helm rollback` one revision, confirm with `helm history`.

**Stretch:** Run ChartMuseum in Docker; add repo and install from `http://localhost:8080`.

---

## 10. DevOps connections

- **Artifact promotion:** Dev pushes chart `0.3.0` to staging registry; prod pipeline only pulls signed `0.3.0` after approval.
- **Immutable infra:** Never `helm install` from random Git SHAs in prod—use versioned `.tgz` or OCI digest.
- **Change management:** `helm diff` output attached to change tickets.

---

## Quick reference

| Task | Command |
|------|---------|
| Package | `helm package PATH -d OUT` |
| Push OCI | `helm push CHART.tgz oci://REG/ns` |
| Repo index | `helm repo index DIR --url URL` |
| Atomic upgrade | `helm upgrade --atomic --wait` |
| Diff | `helm diff upgrade …` |

**Previous:** [Day 5](../day5/) · **Next:** [Day 7 — Production, CI/CD & GitOps](../day7/)
