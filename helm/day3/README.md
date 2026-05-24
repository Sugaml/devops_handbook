# Day 3 — Go Templates: Logic, Functions & Safe YAML

**Goal:** Write maintainable templates using conditionals, loops, scopes, pipes, and Sprig functions—without producing invalid YAML.

**Time:** 5–7 hours

---

## 1. Template delimiters

Helm uses Go `text/template` with extra functions from [Sprig](https://masterminds.github.io/sprig/):

```yaml
{{ .Values.replicaCount }}           # expression
{{- .Values.replicaCount -}}         # trim whitespace left/right
```

**Whitespace control:** `{{-` and `-}}` prevent blank lines in rendered YAML—use them on `if`/`range` lines.

---

## 2. Conditionals

```yaml
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
# ...
{{- end }}
```

```yaml
{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
{{- else if gt (int .Values.replicaCount) 1 }}
# document only when replicas > 1 without HPA
{{- end }}
```

**Truthy in Helm:** non-empty strings, non-zero numbers, non-empty maps/slices, `true`. `false`, `0`, `""`, `nil` are false.

---

## 3. `with` — narrow scope

```yaml
{{- with .Values.resources }}
resources:
  {{- toYaml . | nindent 12 }}
{{- end }}
```

Inside `with`, `.` is the scoped value—not the root. Use `$.Values` to reach root from nested scope.

---

## 4. `range` — lists and maps

```yaml
# env from list
env:
{{- range .Values.env }}
  - name: {{ .name }}
    value: {{ .value | quote }}
{{- end }}
```

```yaml
# iterate map
{{- range $key, $val := .Values.podAnnotations }}
{{ $key }}: {{ $val | quote }}
{{- end }}
```

`$key` and `$val` are loop variables; `$` prefix marks root-relative variables in nested blocks.

---

## 5. Variables in templates

```yaml
{{- $fullname := include "sample-web.fullname" . }}
metadata:
  name: {{ $fullname }}
```

Reuse expensive includes; keep names lowercase with `$`.

---

## 6. Pipes and quoting

```yaml
image: {{ .Values.image.repository | quote }}
tag: {{ .Values.image.tag | default .Chart.AppVersion | quote }}
```

| Function | Use |
|----------|-----|
| `quote` / `squote` | Safe strings in YAML |
| `default A B` | If B empty, use A |
| `required "msg" .Values.x` | Fail render if missing |
| `trunc 63` | DNS label limits |
| ` nindent 4` | Indent block; leading newline required |
| `toYaml` | Dump struct to YAML |
| `toJson` | Annotations needing JSON |

```yaml
{{- fail "replicaCount must be >= 1" }}
```
Use `fail` for validation (stops `helm template` / install).

---

## 7. `include` vs `template`

```yaml
labels:
  {{- include "sample-web.labels" . | nindent 4 }}
```

- `include` — returns string; can pipe to `nindent`.
- `template` — writes directly; no piping.

Prefer `include` for composable `_helpers.tpl` blocks.

---

## 8. Kubernetes API version guards

```yaml
{{- if .Capabilities.APIVersions.Has "autoscaling/v2" }}
apiVersion: autoscaling/v2
{{- else }}
apiVersion: autoscaling/v2beta2
{{- end }}
```

`.Capabilities.KubeVersion` — semver of cluster; use for feature gates.

---

## 9. Optional blocks pattern

Production charts wrap optional sections:

```yaml
{{- if .Values.livenessProbe }}
livenessProbe:
  {{- toYaml .Values.livenessProbe | nindent 12 }}
{{- end }}
```

Values file documents the expected probe map shape.

---

## 10. Common pitfalls

| Problem | Fix |
|---------|-----|
| `type: {{ .Values.port }}` renders unquoted string that YAML parses wrong | Use `quote` or ensure numeric |
| Extra `---` or blank documents | Remove trailing `range` newlines; use `-}}` |
| `toYaml` wrong indent | Match `nindent` to parent key depth |
| Editing inside `with` breaks `.Values` | Use `$` root: `$.Values.global.env` |

**Debug:**

```bash
helm template dbg ./labs/template-lab -n helm-handbook --debug 2>&1 | less
```

---

## 11. Lab chart — [labs/template-lab](./labs/template-lab/)

Features demonstrated:

- `required` for `image.repository`
- `range` over `env` and `extraVolumes`
- Conditional Ingress
- `fail` when `replicaCount < 1`

```bash
cd /Users/babulaltamang/Documents/devops_handbook/helm/day3/labs/template-lab

helm template test . -n helm-handbook
helm template test . -n helm-handbook --set replicaCount=0    # should fail
helm template test . -n helm-handbook --set ingress.enabled=true
```

**Lab tasks:**

1. Add `podAnnotations` map in `values.yaml`; render them on the Pod template with `range`.
2. Add `topologySpreadConstraints` optional block using `with` + `toYaml`.
3. Use `required` for `service.port` and verify error message when unset.
4. Install chart after successful template: `helm install tpl . -n helm-handbook`

---

## 12. DevOps connections

- **Policy-as-code:** Render in CI; fail on `helm template` before any deploy.
- **DRY:** Shared `_helpers.tpl` across microservice charts → library chart (Day 7).
- **Secrets:** Never template cleartext secrets from `values.yaml` in Git—use External Secrets / Sealed Secrets (Day 7).

---

## Quick reference

| Construct | Syntax |
|-----------|--------|
| If | `{{ if }} … {{ else }} … {{ end }}` |
| With | `{{ with .Values.x }} … {{ end }}` |
| Range | `{{ range .Values.items }}` |
| Include | `{{ include "name" . }}` |
| Root in scope | `$.Values` |

**Previous:** [Day 2](../day2/) · **Next:** [Day 4 — Values, overrides & subcharts](../day4/)
