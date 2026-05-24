# Day 8 — ConfigMaps & Configuration Patterns

**Goal:** Externalize configuration from container images using ConfigMaps, mount as files or env vars, and follow twelve-factor patterns.

**Time:** 4–5 hours

---

## 1. Why ConfigMaps?

| Anti-pattern | Better approach |
|--------------|-----------------|
| Rebuild image for config change | ConfigMap + rolling restart |
| Hardcoded URLs in code | Env vars from ConfigMap |
| Giant env var lists | Mounted config files |

ConfigMaps store **non-sensitive** data. Secrets (Day 9) for credentials.

---

## 2. Create ConfigMaps

```bash
# Literal
kubectl create configmap app-config \
  --from-literal=APP_ENV=staging \
  --from-literal=LOG_LEVEL=debug \
  -n handbook-lab

# From file
kubectl create configmap nginx-conf --from-file=nginx.conf -n handbook-lab

# From directory
kubectl create configmap app-files --from-file=./config/ -n handbook-lab
```

Declarative:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: handbook-lab
data:
  APP_ENV: staging
  LOG_LEVEL: info
  app.properties: |
    server.port=8080
    server.host=0.0.0.0
```

---

## 3. Consume as environment variables

```yaml
spec:
  containers:
    - name: app
      image: myapp:1.0
      env:
        - name: APP_ENV
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: APP_ENV
      envFrom:
        - configMapRef:
            name: app-config   # all keys as env vars
```

**Note:** ConfigMap changes do **not** auto-reload env vars — Pod restart required.

---

## 4. Mount as volumes

```yaml
spec:
  volumes:
    - name: config
      configMap:
        name: app-config
        items:
          - key: app.properties
            path: app.properties
  containers:
    - name: app
      volumeMounts:
        - name: config
          mountPath: /etc/config
          readOnly: true
```

SubPath for single file without overwriting directory:

```yaml
volumeMounts:
  - name: nginx-conf
    mountPath: /etc/nginx/nginx.conf
    subPath: nginx.conf
```

---

## 5. Immutable ConfigMaps (K8s 1.21+)

```yaml
immutable: true
```

Prevents accidental updates; change requires new ConfigMap name + rollout.

---

## 6. Hot reload pattern

For mounted files, some apps watch filesystem (nginx `reload`). For env-based apps:

```bash
kubectl rollout restart deployment/web -n handbook-lab
```

Or use [Reloader](https://github.com/stakater/Reloader) operator in production.

---

## 7. Lab — Day 8

1. Create ConfigMap `web-config` with key `index.html` containing custom HTML.
2. Mount as volume at `/usr/share/nginx/html/index.html` using subPath on nginx Deployment.
3. Update ConfigMap content; verify nginx still serves old content until restart.
4. `kubectl rollout restart deployment/web`; verify new content.
5. Use `envFrom` to inject all keys into a busybox pod and print env.

**Stretch:** Split dev/prod ConfigMaps; use Kustomize `configMapGenerator` (optional reading).

---

## 8. DevOps connections

- **Feature flags:** Often served from external service; static toggles fit ConfigMaps.
- **Helm:** Values render into ConfigMap templates (Day 18).
- **Size limit:** 1 MiB per ConfigMap — large configs use volumes or external stores.

---

## Quick reference

| Task | Command |
|------|---------|
| Create from literal | `kubectl create cm NAME --from-literal=k=v` |
| Create from file | `kubectl create cm NAME --from-file=path` |
| View | `kubectl get cm NAME -o yaml` |
| Restart after change | `kubectl rollout restart deploy/NAME` |

**Next:** [Day 9 — Secrets](../day9/)
