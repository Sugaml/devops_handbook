# Day 21 — Init Containers, Sidecars & Multi-Container Patterns

**Goal:** Use init containers for setup/ordering, sidecars for cross-cutting concerns, and apply the ambassador/adapter patterns.

**Time:** 5 hours

---

## 1. Init containers

Run **sequentially** to completion before app containers start.

```yaml
spec:
  initContainers:
    - name: wait-for-db
      image: busybox:1.36
      command:
        - sh
        - -c
        - |
          until nc -z postgres 5432; do echo waiting; sleep 2; done
    - name: migrate
      image: myapp:1.0
      command: ["./migrate", "up"]
      envFrom:
        - secretRef:
            name: db-credentials
  containers:
    - name: app
      image: myapp:1.0
```

Use cases: wait for dependencies, DB migrations, download config/assets.

---

## 2. Sidecar pattern

Runs alongside app container in same Pod — shared network and volumes.

| Sidecar role | Example |
|--------------|---------|
| Log shipping | Fluent Bit → Elasticsearch |
| Proxy | Envoy, nginx local proxy |
| Sync | config sync, vault agent |
| Mesh | Istio proxy injected |

```yaml
containers:
  - name: app
    image: nginx:1.27-alpine
    volumeMounts:
      - name: logs
        mountPath: /var/log/nginx
  - name: log-collector
    image: fluent/fluent-bit:3.0
    volumeMounts:
      - name: logs
        mountPath: /var/log/nginx
        readOnly: true
```

---

## 3. Ambassador pattern

Proxy Pod talks to external world on behalf of app — simplified local connection.

```yaml
# App connects

  - name: app
    env:
      - name: PROXY_HOST
        value: "127.0.0.1:6379"
  - name: redis-proxy
    image: haproxy:2.9
    # forwards localhost:6379 → redis.external:6379
```

---

## 4. Adapter pattern

Transform output — e.g. normalize metrics format.

Sidecar scrapes app metrics on localhost, exposes Prometheus format on :9090.

---

## 5. Native sidecar containers (K8s 1.28+ beta)

```yaml
initContainers:
  - name: sidecar
    restartPolicy: Always   # sidecar stays running with app
    image: ...
```

Check your cluster version and feature gates for sidecar container semantics.

---

## 6. Lab — Day 21

1. Deploy Pod with initContainer that writes file to `emptyDir`; app container reads it.
2. Add second initContainer that must complete after first (chain two inits).
3. Build nginx + busybox `tail -F` sidecar; logs visible via sidecar.
4. Simulate failed init (bad command); observe Pod stuck in `Init:N/M`.
5. Replace init wait loop with proper readiness on dependency Service (preferred prod pattern).

**Stretch:** Read Istio sidecar injection labels — `sidecar.istio.io/inject: "true"`.

---

## 7. DevOps connections

- **Service mesh:** Sidecars injected automatically — understand resource overhead (+50–100m CPU per pod).
- **Migrations:** Job or initContainer debate — Jobs better for long migrations with retry.
- **Security:** Sidecars can hold mTLS certs without app changes.

---

## Quick reference

| Pattern | When |
|---------|------|
| Init | One-time setup, ordering |
| Sidecar | Continuous helper process |
| Ambassador | Simplify external access |
| Adapter | Transform monitor/output |

**Next:** [Day 22 — CRDs & operators](../day22/)
