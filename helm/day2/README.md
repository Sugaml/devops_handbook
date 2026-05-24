# Day 2 — Chart Anatomy, `helm create` & Local Releases

**Goal:** Read a chart like a pro, scaffold with `helm create`, render manifests locally, and install/upgrade your own chart from disk.

**Time:** 4–6 hours

---

## 1. Standard chart layout

```
my-chart/
├── Chart.yaml          # Metadata (name, version, dependencies)
├── values.yaml         # Default inputs
├── charts/             # Subchart .tgz or subdirs (dependencies)
├── templates/          # Go templates → Kubernetes YAML
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── _helpers.tpl    # Named templates (Day 5)
│   ├── NOTES.txt       # Post-install hints
│   └── tests/          # Helm test pods (Day 5)
└── .helmignore         # Files excluded from package
```

| File | Purpose |
|------|---------|
| `Chart.yaml` | `apiVersion: v2`, name, version, appVersion, dependencies |
| `values.yaml` | Document every key teams may override |
| `templates/` | Only files ending in `.yaml`, `.yml`, `.tpl` render |
| `charts/` | Vendored dependencies after `helm dependency build` |

---

## 2. `Chart.yaml` essentials

```yaml
apiVersion: v2
name: sample-web
description: Handbook demo web chart
type: application
version: 0.1.0        # chart version (SemVer)
appVersion: "1.0.0"   # informational; often image tag
```

- **chart version** — bump when templates or default values change.
- **appVersion** — displayed in labels; does not auto-update images unless your templates use it.

---

## 3. Scaffold and trim

```bash
cd /Users/babulaltamang/Documents/devops_handbook/helm/day2/labs
helm create my-web
cd my-web
tree -L 2
```

Default chart is large. For learning, delete unused templates (`hpa.yaml`, `ingress.yaml` if unused) and simplify `values.yaml`.

Reference implementation: [labs/sample-web](./labs/sample-web/).

```bash
helm lint ./labs/sample-web
helm template handbook-release ./labs/sample-web -n helm-handbook
```

---

## 4. `values.yaml` → templates (first look)

In `templates/deployment.yaml`, Helm injects values:

```yaml
replicas: {{ .Values.replicaCount }}
image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
```

The root object `.` includes:

| Field | Meaning |
|-------|---------|
| `.Values` | Merged values (defaults + files + `--set`) |
| `.Release` | Name, namespace, service, revision |
| `.Chart` | Contents of `Chart.yaml` |
| `.Capabilities` | K8s version, API groups supported |
| `.Template` | Current template name (for debugging) |

---

## 5. `helm template` vs `helm install`

```bash
# Offline render — no release, no cluster write
helm template myrel ./labs/sample-web \
  -n helm-handbook \
  -f ./labs/sample-web/values.yaml \
  --set replicaCount=3 \
  > /tmp/rendered.yaml

# Validate YAML
kubectl apply --dry-run=client -f /tmp/rendered.yaml
```

| Command | Cluster | Release record |
|---------|---------|----------------|
| `helm template` | Optional dry-run only | No |
| `helm install --dry-run` | Server may validate | No (or simulated) |
| `helm install` | Yes | Yes |

---

## 6. Install from filesystem

```bash
helm install web1 ./labs/sample-web -n helm-handbook --create-namespace

kubectl get deploy,svc -n helm-handbook
kubectl port-forward -n helm-handbook svc/web1-sample-web 8080:80 &
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/
```

---

## 7. Upgrade patterns

```bash
# File override
cat > /tmp/web-prod.yaml <<'EOF'
replicaCount: 3
image:
  tag: "1.0.1"
EOF

helm upgrade web1 ./labs/sample-web -n helm-handbook -f /tmp/web-prod.yaml

# Set one key
helm upgrade web1 ./labs/sample-web -n helm-handbook --reuse-values --set replicaCount=2

helm get values web1 -n helm-handbook --all   # includes defaults
```

---

## 8. `.helmignore`

Exclude VCS, IDE, and secrets from packaged charts:

```
.git/
.idea/
*.md
secrets/
```

Never package `.env` or kubeconfigs into a chart artifact.

---

## 9. `helm lint`

```bash
helm lint ./labs/sample-web
helm lint ./labs/sample-web --set replicaCount=0   # may warn on probes/resources
```

Fixes chart issues before CI. Pair with `kubeconform` or `kubectl apply --dry-run=server` in pipelines (Day 7).

---

## 10. Lab — Day 2

1. `helm create lab-app` in `/tmp`; list every file under `templates/`.
2. Compare your tree to [labs/sample-web](./labs/sample-web/); align `values.yaml` keys `replicaCount`, `image.repository`, `image.tag`, `service.port`.
3. `helm template lab ./labs/sample-web -n helm-handbook --debug | less`
4. `helm install lab ./labs/sample-web -n helm-handbook`
5. Upgrade with `-f` changing `replicaCount`; confirm with `kubectl get deploy -n helm-handbook`.
6. `helm uninstall lab -n helm-handbook`

**Stretch:** Add `podLabels: { team: platform }` to `values.yaml` and wire it into Deployment metadata in a fork of the chart.

---

## 11. DevOps connections

- **Chart as artifact:** Version chart in CI, push `.tgz` to OCI/Harbor (Day 6).
- **Values per env:** `values-dev.yaml`, `values-prod.yaml` — same chart, different files.
- **Code review:** PRs review `values.yaml` + template diffs via `helm template` output.

---

## Quick reference

| Task | Command |
|------|---------|
| Scaffold | `helm create NAME` |
| Lint | `helm lint PATH` |
| Render | `helm template REL PATH -n NS` |
| Local install | `helm install REL PATH -n NS` |

**Previous:** [Day 1](../day1/) · **Next:** [Day 3 — Go templating in depth](../day3/)
