# Day 30 — Capstone: Full Stack on Kubernetes

**Goal:** Deploy a production-style three-tier application — frontend, API, database — with Ingress, secrets, persistence, monitoring hooks, and GitOps-ready manifests.

**Time:** 8–10 hours

---

## 1. Architecture

```
                    ┌─────────────┐
   Browser ────────▶│   Ingress   │  TLS (cert-manager optional)
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       ┌─────────────┐           ┌─────────────┐
       │  frontend   │           │     api     │
       │  (nginx)    │──────────▶│  (http-echo │
       │  Deployment│  /api    │  + env)     │
       └─────────────┘           └──────┬──────┘
                                        │
                                        ▼
                                 ┌─────────────┐
                                 │  postgres   │
                                 │ StatefulSet │
                                 │  + PVC      │
                                 └─────────────┘
```

Namespace: `handbook-capstone`

---

## 2. Project structure

Create this layout in your lab repo:

```
kubernetes/day30/
  README.md
  manifests/
    namespace.yaml
    postgres/
      secret.yaml
      statefulset.yaml
      service.yaml
    api/
      configmap.yaml
      deployment.yaml
      service.yaml
    frontend/
      configmap.yaml
      deployment.yaml
      service.yaml
    ingress.yaml
    networkpolicy.yaml
    hpa.yaml
    pdb.yaml
```

---

## 3. Namespace and database

```yaml
# manifests/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: handbook-capstone
  labels:
    pod-security.kubernetes.io/enforce: baseline
```

```yaml
# postgres/secret.yaml — use stringData in lab only; never commit real passwords
apiVersion: v1
kind: Secret
metadata:
  name: postgres-credentials
  namespace: handbook-capstone
type: Opaque
stringData:
  POSTGRES_USER: app
  POSTGRES_PASSWORD: changeme-capstone
  POSTGRES_DB: appdb
```

```yaml
# postgres/statefulset.yaml (simplified)
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: handbook-capstone
spec:
  serviceName: postgres-headless
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          ports:
            - containerPort: 5432
          envFrom:
            - secretRef:
                name: postgres-credentials
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              memory: 512Mi
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 5Gi
```

Fix typo POSTGRES,PASSWORD -> POSTGRES_PASSWORD in actual file... I'll write correct version in the manifest folder if I create sample files. For README content I'll fix the typo.

---

## 4. API layer

Use a simple API image; for lab, http-echo simulates backend:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: handbook-capstone
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
        - name: api
          image: hashicorp/http-echo:1.0
          args:
            - "-text=Capstone API OK"
            - "-listen=:8080"
          ports:
            - containerPort: 8080
          readinessProbe:
            httpGet:
              path: /
              port: 8080
          livenessProbe:
            httpGet:
              path: /
              port: 8080
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
---
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: handbook-capstone
spec:
  selector:
    app: api
  ports:
    - port: 8080
      targetPort: 8080
```

**Production upgrade path:** Replace with real API connecting to `postgres:5432` via env from Secret.

---

## 5. Frontend

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: frontend-html
  namespace: handbook-capstone
data:
  index.html: |
    <!DOCTYPE html>
    <html><body>
    <h1>DevOps Handbook Capstone</h1>
    <p>API status: <a href="/api/">check /api</a></p>
    </body></html>
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: handbook-capstone
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
        - name: nginx
          image: nginx:1.27-alpine
          ports:
            - containerPort: 80
          volumeMounts:
            - name: html
              mountPath: /usr/share/nginx/html/index.html
              subPath: index.html
          readinessProbe:
            httpGet:
              path: /
              port: 80
      volumes:
        - name: html
          configMap:
            name: frontend-html
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: handbook-capstone
spec:
  selector:
    app: frontend
  ports:
    - port: 80
```

---

## 6. Ingress routing

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: capstone
  namespace: handbook-capstone
spec:
  ingressClassName: nginx
  rules:
    - host: capstone.localdev.me
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api
                port:
                  number: 8080
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 80
```

```bash
echo "127.0.0.1 capstone.localdev.me" | sudo tee -a /etc/hosts
curl http://capstone.localdev.me/api/
curl http://capstone.localdev.me/
```

---

## 7. Reliability and scale

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api
  namespace: handbook-capstone
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 2
  maxReplicas: 5
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
---
# pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-pdb
  namespace: handbook-capstone
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: api
```

---

## 8. NetworkPolicy (optional hardening)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-ingress
  namespace: handbook-capstone
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes: [Ingress]
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8080
```

---

## 9. Deploy end-to-end

```bash
kubectl apply -f manifests/namespace.yaml
kubectl apply -f manifests/postgres/
kubectl wait --for=condition=ready pod -l app=postgres -n handbook-capstone --timeout=120s
kubectl apply -f manifests/api/
kubectl apply -f manifests/frontend/
kubectl apply -f manifests/ingress.yaml
kubectl apply -f manifests/hpa.yaml
kubectl apply -f manifests/pdb.yaml

kubectl get all -n handbook-capstone
kubectl get ingress -n handbook-capstone
```

---

## 10. Capstone deliverables checklist

- [ ] All manifests in Git repository
- [ ] README with architecture diagram and deploy steps
- [ ] Secrets not committed (use Sealed Secrets or `.gitignore`)
- [ ] Resource requests on every container
- [ ] Probes on every Deployment
- [ ] Ingress routes `/` and `/api`
- [ ] Postgres data survives Pod restart
- [ ] HPA and PDB applied
- [ ] Optional: Argo CD Application (Day 23)
- [ ] Optional: Grafana dashboard for namespace (Day 25)
- [ ] Optional: Helm chart wrapping manifests (Day 18)

---

## 11. Presentation exercise

Explain in 10 minutes to a colleague:

1. Why StatefulSet for Postgres?
2. What breaks if you delete the PVC?
3. How would you promote this from kind to EKS?
4. What is your rollback plan?

---

## 12. What you learned in 30 days

| Week | Skills |
|------|--------|
| 1 | Core objects, networking ingress path |
| 2 | Config, secrets, RBAC, batch workloads |
| 3 | Storage, Helm, reliability probes, scaling |
| 4 | GitOps, security, ops, capstone |

**Keep going:** Gateway API, service mesh, Cluster API, eBPF (Cilium), platform engineering books.

---

## Quick reference

| Task | Command |
|------|---------|
| Deploy all | `kubectl apply -f manifests/ -R` |
| Capstone NS | `handbook-capstone` |
| Test ingress | `curl -H "Host: capstone.localdev.me" http://localhost:8080/api/` |
| Tear down | `kubectl delete ns handbook-capstone` |

**Congratulations — you completed the 30-day Kubernetes handbook.**

[Back to handbook index](../README.md)
