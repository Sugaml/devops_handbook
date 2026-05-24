# Day 7 — Ingress & HTTP Routing

**Goal:** Route external HTTP/HTTPS traffic to Services with Ingress, install an Ingress controller, and configure TLS and path-based routing.

**Time:** 5–6 hours

---

## 1. Ingress vs Service

| Layer | Handles |
|-------|---------|
| **LoadBalancer Service** | L4 TCP/UDP, one LB per Service (often) |
| **Ingress** | L7 HTTP routing, host/path rules, TLS termination |

```
Internet → Ingress Controller → Ingress rules → Service → Pods
```

Ingress is a **spec**; you need a **controller** (nginx, traefik, AWS ALB, etc.) to enforce it.

---

## 2. Install NGINX Ingress on kind

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

kubectl get pods -n ingress-nginx
```

kind config from Day 1 should map host port 8080 → controller NodePort or use:

```bash
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80
```

---

## 3. Basic Ingress manifest

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
  namespace: handbook-lab
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: web.localdev.me
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web
                port:
                  number: 80
```

```bash
# Add to /etc/hosts: 127.0.0.1 web.localdev.me
curl -H "Host: web.localdev.me" http://localhost:8080/
```

---

## 4. Path-based routing

Deploy two backends (`web-v1`, `web-v2` Services) and split traffic:

```yaml
spec:
  rules:
    - host: shop.localdev.me
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
                name: web
                port:
                  number: 80
```

`pathType`: `Prefix`, `Exact`, or `ImplementationSpecific` (controller-dependent).

---

## 5. TLS termination

```yaml
spec:
  tls:
    - hosts:
        - web.localdev.me
      secretName: web-tls
```

Create TLS Secret (Day 9):

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt -subj "/CN=web.localdev.me"

kubectl create secret tls web-tls --cert=tls.crt --key=tls.key -n handbook-lab
```

Production: use **cert-manager** with Let's Encrypt.

---

## 6. IngressClass

```yaml
spec:
  ingressClassName: nginx
```

Links Ingress to a specific controller implementation — required pattern on modern clusters.

---

## 7. Annotations (NGINX examples)

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/rate-limit: "100"
```

Annotations are controller-specific — check your controller docs.

---

## 8. Debugging Ingress

```bash
kubectl get ingress -n handbook-lab
kubectl describe ingress web -n handbook-lab
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller --tail=50

# Common issues
# - 404: wrong path or Service port
# - 503: no ready endpoints
# - Certificate error: Secret missing or wrong host
```

---

## 9. Lab — Day 7

1. Install ingress-nginx on your kind cluster.
2. Expose Day 5 `web` Deployment via Ingress on host `web.localdev.me`.
3. Add second Deployment `api` (http-echo); route `/api` to api, `/` to web on same host.
4. Generate self-signed cert; enable HTTPS on Ingress.
5. Test with `curl -k https://web.localdev.me` (via port-forward or hosts file).

**Stretch:** Install [cert-manager](https://cert-manager.io/) in dry-run mode and read CRDs — full setup optional locally.

---

## 10. DevOps connections

- **Gateway API** (successor to Ingress) — richer L4/L7; learn after mastering Ingress.
- **WAF / CDN:** Cloudflare or AWS CloudFront often sit in front of Ingress.
- **Internal-only apps:** Internal Ingress or private LoadBalancer + no public DNS.

---

## Quick reference

| Task | Command |
|------|---------|
| List ingress | `kubectl get ing -n handbook-lab` |
| Controller logs | `kubectl logs -n ingress-nginx deploy/...` |
| TLS secret | `kubectl create secret tls NAME --cert= --key=` |
| Test host header | `curl -H "Host: app.example.com" http://IP/` |

**Next:** [Day 8 — ConfigMaps](../day8/)
