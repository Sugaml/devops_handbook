# Day 5 — Helpers, Hooks, Tests & Chart UX

**Goal:** Standardize naming and labels with `_helpers.tpl`, run lifecycle hooks safely, ship chart tests, and polish operator experience (`NOTES.txt`, README).

**Time:** 5–6 hours

---

## 1. `_helpers.tpl` — named templates

Centralize DNS-safe names and recommended labels:

```yaml
{{- define "mychart.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
```

**Kubernetes recommended labels** (use in every resource):

| Label | Source |
|-------|--------|
| `app.kubernetes.io/name` | Chart or `nameOverride` |
| `app.kubernetes.io/instance` | `.Release.Name` |
| `app.kubernetes.io/version` | `.Chart.AppVersion` |
| `app.kubernetes.io/managed-by` | `.Release.Service` (`Helm`) |
| `helm.sh/chart` | `chart-version` |

See [labs/hooks-demo](./labs/hooks-demo/) for full helper set.

---

## 2. `nameOverride` and `fullnameOverride`

```yaml
# values.yaml
nameOverride: api
fullnameOverride: payments-api-prod
```

Allows multiple charts named `web` in one release without collision when combined with release name logic in `fullname` helper.

---

## 3. Helm hooks

Hooks are annotated resources that run at defined points:

| Annotation value | When |
|------------------|------|
| `pre-install` | Before resources created |
| `post-install` | After install |
| `pre-upgrade` | Before upgrade |
| `post-upgrade` | After upgrade |
| `pre-delete` | Before uninstall |
| `post-delete` | After delete |
| `test` | When `helm test` runs |

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ include "hooks-demo.fullname" . }}-migrate
  annotations:
    "helm.sh/hook": post-install,post-upgrade
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: migrate
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          command: ["sh", "-c", "echo migrate && sleep 2"]
```

| Annotation | Purpose |
|------------|---------|
| `hook-weight` | Order (lower runs first) |
| `hook-delete-policy` | When to delete hook resources |

**Caution:** Failed hooks block release; test hooks in dev clusters first.

```bash
helm install hd ./labs/hooks-demo -n helm-handbook --wait --timeout 5m
kubectl get jobs -n helm-handbook
```

---

## 4. `helm test`

`templates/tests/test-connection.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: {{ include "hooks-demo.fullname" . }}-test
  annotations:
    "helm.sh/hook": test
spec:
  restartPolicy: Never
  containers:
    - name: wget
      image: busybox:1.36
      command: ['wget']
      args: ['{{ include "hooks-demo.fullname" . }}:{{ .Values.service.port }}']
```

```bash
helm test hd -n helm-handbook
kubectl logs -n helm-handbook -l helm.sh/hook=test
```

Tests should be **non-destructive** and idempotent.

---

## 5. `NOTES.txt`

Post-install instructions shown via `helm get notes`:

```text
export APP_HOST=$(kubectl get svc ...)
echo "Open http://$APP_HOST"
```

Use `{{- if eq .Values.service.type "NodePort" }}` branches like Day 2 sample-web.

---

## 6. Chart README and schema (optional)

`values.schema.json` — JSON Schema validation of values (Helm 3):

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "properties": {
    "replicaCount": { "type": "integer", "minimum": 1 }
  },
  "required": ["image"]
}
```

CI: `helm lint` + schema tools catch typos before deploy.

---

## 7. Resource policy annotations

```yaml
metadata:
  annotations:
    "helm.sh/resource-policy": keep
```

On uninstall, `keep` prevents deletion (e.g. PVCs). Document data retention implications.

---

## 8. Lab — Day 5

Chart: [labs/hooks-demo](./labs/hooks-demo/)

1. Install with `--wait`; watch hook Job complete: `kubectl get jobs -n helm-handbook -w`
2. Upgrade with changed `migrationTag` value; confirm post-upgrade hook runs again.
3. Run `helm test`; capture logs on failure.
4. Read `helm get notes` and follow port-forward instructions.
5. Uninstall; verify hook delete policy removed Jobs.

**Stretch:** Add `pre-delete` hook that logs cleanup (Job must finish before release deletes).

---

## 9. DevOps connections

- **DB migrations:** `post-upgrade` hooks are common; many teams prefer init Job in GitOps (Argo Sync waves) instead.
- **Smoke tests:** `helm test` in CI after deploy to staging.
- **Labels:** Consistent helpers enable Prometheus/Grafana service discovery.

---

## Quick reference

| Task | Command |
|------|---------|
| Wait for ready | `helm install --wait --timeout 10m` |
| Run tests | `helm test RELEASE -n NS` |
| Hook resources | `kubectl get jobs,pods -l helm.sh/hook` |

**Previous:** [Day 4](../day4/) · **Next:** [Day 6 — Package, publish & rollback](../day6/)
