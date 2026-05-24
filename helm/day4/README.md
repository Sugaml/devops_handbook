# Day 4 — Values, Overrides, Subcharts & Dependencies

**Goal:** Master value precedence, global vs local keys, umbrella charts, and the dependency workflow (`helm dependency update` / `build`).

**Time:** 5–7 hours

---

## 1. Value merge order (lowest → highest priority)

1. Chart `values.yaml` defaults
2. Parent chart values (for subcharts, under key = subchart name or alias)
3. User-supplied files (`-f` / `--values`), last file wins
4. `--set` / `--set-string` / `--set-file`

```bash
helm install app ./chart \
  -f values.yaml \
  -f values-prod.yaml \
  --set replicaCount=5
```

Verify effective values:

```bash
helm get values RELEASE -n NS --all
helm template REL ./chart -f values-prod.yaml --debug 2>&1 | head
```

---

## 2. Structuring environment files

```
deploy/
├── values.yaml              # shared defaults
├── values-dev.yaml
├── values-staging.yaml
└── values-prod.yaml
```

```yaml
# values-prod.yaml
replicaCount: 5
image:
  tag: "2.4.1"
resources:
  requests:
    cpu: 500m
    memory: 512Mi
```

**Practice:** Only differences per env—avoid copying entire files.

---

## 3. `--set` grammar

```bash
helm upgrade api ./chart --set replicaCount=3
helm upgrade api ./chart --set 'podAnnotations.environment=prod'
helm upgrade api ./chart --set-json 'podLabels={"team":"payments"}'
helm upgrade api ./chart --set-file config=./config.json
```

| Flag | Type coercion |
|------|----------------|
| `--set` | bool/number if parseable |
| `--set-string` | always string |
| `--set-json` | JSON object/array |

Prefer files for complex structures; `--set` for CI one-offs.

---

## 4. Global values (subcharts)

Parent `values.yaml`:

```yaml
global:
  environment: production
  imageRegistry: registry.example.com

redis:
  enabled: true
  auth:
    password: ""   # use secret in prod
```

Subchart templates read:

```yaml
image: {{ .Values.global.imageRegistry }}/redis:{{ .Values.image.tag }}
```

Convention: document `global` keys in parent README; subcharts use `{{- with .Values.global }}` defensively.

---

## 5. Declaring dependencies

`Chart.yaml`:

```yaml
dependencies:
  - name: redis
    version: "18.x.x"
    repository: https://charts.bitnami.com/bitnami
    condition: redis.enabled
    tags:
      - cache
```

| Field | Effect |
|-------|--------|
| `condition` | Install only if `redis.enabled` true in values |
| `tags` | `helm install --set tags.cache=true` enables tagged deps |
| `alias` | Values under alias key instead of chart name |

```bash
cd ./labs/umbrella-demo
helm dependency update    # fetch to charts/*.tgz
# or: helm dependency build   # uses Chart.lock
helm dependency list
```

---

## 6. Umbrella chart pattern

```
umbrella-demo/
├── Chart.yaml
├── values.yaml
├── charts/              # after dependency update
│   └── redis-18.x.x.tgz
└── templates/           # optional app-specific resources
```

Parent enables/disables children:

```yaml
redis:
  enabled: true
  architecture: standalone

sample-web:
  replicaCount: 2
```

Reference lab: [labs/umbrella-demo](./labs/umbrella-demo/).

After clone, ensure dependencies are vendored:

```bash
cd ./labs/umbrella-demo
helm dependency build    # uses Chart.lock → charts/*.tgz
helm dependency list
```

```bash
helm template umbrella ./labs/umbrella-demo -n helm-handbook
helm install umbrella ./labs/umbrella-demo -n helm-handbook
```

---

## 7. Local subchart (no remote repo)

```
parent/
├── Chart.yaml
├── charts/
│   └── mylib/           # subchart directory
│       ├── Chart.yaml
│       └── templates/
```

`Chart.yaml` dependencies entry with `repository: file://../mylib` or vendored copy—common for monorepos.

---

## 8. `export-values` (Helm 3.13+)

Parent can pass values to children explicitly via `Chart.yaml` `import-values` / `export-values`—use when global conventions are insufficient. Check your Helm version: `helm version`.

---

## 9. Lab — Day 4

Using [labs/umbrella-demo](./labs/umbrella-demo/):

1. Run `helm dependency update` in the umbrella directory.
2. `helm template u ./labs/umbrella-demo -n helm-handbook -f ./labs/umbrella-demo/values-dev.yaml`
3. Install with redis disabled: `--set redis.enabled=false` — confirm fewer resources.
4. Install with redis enabled; `kubectl get pods -n helm-handbook`.
5. Create `values-prod.yaml` overriding only `sample-web.replicaCount` and redis memory; upgrade release.

**Stretch:** Add `tags` in `Chart.yaml` and install with `--set tags.monitoring=true` if you add a optional dependency.

---

## 10. DevOps connections

- **Single deploy unit:** Umbrella chart = one Helm release for app + cache + ingress.
- **Version pinning:** Commit `Chart.lock` to Git; CI runs `helm dependency build`.
- **Blast radius:** Disabling subchart via `condition` beats maintaining two separate charts.

---

## Quick reference

| Task | Command |
|------|---------|
| Fetch deps | `helm dependency update` |
| Build from lock | `helm dependency build` |
| List deps | `helm dependency list` |
| All values | `helm get values REL -a` |

**Previous:** [Day 3](../day3/) · **Next:** [Day 5 — Hooks, tests & helpers](../day5/)
