# Day 6 — Services: ClusterIP, NodePort & LoadBalancer

**Goal:** Expose Pods with Services, understand kube-proxy and DNS, and choose the right Service type for each environment.

**Time:** 5 hours

---

## 1. Why Services?

Pods are ephemeral — IP changes on restart. **Service** provides a stable virtual IP and DNS name that load-balances to ready Pod endpoints.

```
Client → Service (ClusterIP 10.96.x.x) → Endpoints (Pod IPs:ports)
              ↑
         kube-proxy rules
```

---

## 2. Service types

| Type | Reachable from | Typical use |
|------|----------------|-------------|
| **ClusterIP** | Inside cluster only | Internal microservices |
| **NodePort** | `<NodeIP>:30000-32767` | Dev, bare-metal LB front |
| **LoadBalancer** | Cloud LB external IP | Public APIs (cloud) |
| **ExternalName** | CNAME to external DNS | Legacy DB hostname |

---

## 3. ClusterIP manifest

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
  namespace: handbook-lab
spec:
  type: ClusterIP
  selector:
    app: web
  ports:
    - name: http
      port: 80          # Service port
      targetPort: 80     # Pod containerPort
      protocol: TCP
```

```bash
kubectl apply -f manifests/web-service.yaml
kubectl get svc,endpoints -n handbook-lab
kubectl describe svc web -n handbook-lab
```

---

## 4. DNS in Kubernetes

CoreDNS resolves:

```
<service>.<namespace>.svc.cluster.local
web.handbook-lab.svc.cluster.local
```

Same namespace short names: `web`, `web.handbook-lab`

```bash
kubectl run dns-test --rm -it --restart=Never --image=busybox:1.36 -n handbook-lab -- \
  nslookup web.handbook-lab.svc.cluster.local
```

---

## 5. NodePort and kind port mapping

```yaml
spec:
  type: NodePort
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30080   # optional; must be 30000-32767
```

With kind extraPortMappings (Day 1 config), host `8080` → node `30080`.

```bash
curl http://localhost:8080   # from host with kind mapping
```

---

## 6. Headless Services

No ClusterIP — DNS returns Pod A records directly (StatefulSets, Day 11).

```yaml
spec:
  clusterIP: None
  selector:
    app: web
```

```bash
kubectl get svc web-headless -n handbook-lab
# DNS: web-headless.handbook-lab.svc.cluster.local → pod IPs
```

---

## 7. Endpoints and EndpointSlices

```bash
kubectl get endpoints web -n handbook-lab -o yaml
kubectl get endpointslice -n handbook-lab
```

Endpoints update when Pod readiness changes — misconfigured readiness = no traffic (Day 19).

---

## 8. Session affinity

```yaml
spec:
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
```

Use sparingly; prefer stateless apps or shared session store.

---

## 9. Lab — Day 6

1. Ensure Deployment `web` (Day 5) is running; create ClusterIP Service.
2. From a debug pod, `curl http://web.handbook-lab.svc.cluster.local`.
3. Scale deployment to 0; observe empty endpoints; scale back to 3.
4. Change Service to NodePort; access from host (kind port map or `minikube service`).
5. Create headless Service; compare DNS with `nslookup`.
6. Deliberately mismatch selector (`app: wrong`); verify no endpoints.

**Stretch:** `kubectl port-forward svc/web 8080:80 -n handbook-lab` for local dev without NodePort.

---

## 10. DevOps connections

- **Ingress** (Day 7) sits in front of ClusterIP Services for HTTP routing.
- **Service mesh** (Istio/Linkerd) adds mTLS and traffic policies without changing Service objects.
- **Cloud LB cost:** One LoadBalancer per Service adds up — Ingress or shared LB controllers reduce sprawl.

---

## Quick reference

| Task | Command |
|------|---------|
| List services | `kubectl get svc -n handbook-lab` |
| Endpoints | `kubectl get endpoints NAME` |
| Port forward svc | `kubectl port-forward svc/NAME LOCAL:PORT` |
| DNS test | `nslookup svc.ns.svc.cluster.local` |

**Next:** [Day 7 — Ingress](../day7/)
