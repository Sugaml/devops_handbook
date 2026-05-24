# Day 15 — NetworkPolicies & Pod Networking

**Goal:** Restrict Pod-to-Pod traffic with NetworkPolicies, understand default allow vs deny models, and test connectivity.

**Time:** 5 hours

---

## 1. Default cluster behavior

Without NetworkPolicy, **all Pod traffic is allowed** (depending on CNI). NetworkPolicy adds firewall rules at the Pod network interface level.

Requires CNI that enforces NetworkPolicy (Calico, Cilium, Weave — kind uses kindnet which has **limited** NP support; use Calico for full lab):

```bash
# Optional: kind with Calico for NetworkPolicy labs
# See: https://docs.projectcalico.org/getting-started/kubernetes/kind
```

---

## 2. NetworkPolicy structure

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: handbook-lab
spec:
  podSelector: {}      # all pods in namespace
  policyTypes:
    - Ingress
  # no ingress rules = deny all ingress
```

---

## 3. Allow frontend → backend only

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-policy
  namespace: handbook-lab
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - protocol: TCP
          port: 8080
```

---

## 4. Namespace selector & ipBlock

```yaml
ingress:
  - from:
      - namespaceSelector:
          matchLabels:
            kubernetes.io/metadata.name: monitoring
        podSelector:
          matchLabels:
            app: prometheus
  - from:
      - ipBlock:
          cidr: 10.0.0.0/8
          except:
            - 10.0.1.0/24
```

---

## 5. Egress policies

```yaml
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
    - Egress
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: database
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - namespaceSelector: {}
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
```

Always allow DNS egress when locking down egress.

---

## 6. Testing connectivity

```bash
kubectl run test --rm -it --restart=Never --image=nicolaka/netshoot -n handbook-lab -- bash
# inside: curl, nc -zv, ping
kubectl exec -it POD -- curl http://backend:8080
```

---

## 7. Lab — Day 15

1. Deploy `frontend` and `backend` Deployments with labels.
2. Verify curl works without NetworkPolicy.
3. Apply `deny-all-ingress`; confirm traffic breaks.
4. Apply policy allowing only `frontend` → `backend:8080`.
5. Add egress policy on `backend` denying all except frontend CIDR/pod.

**Note:** If kindnet limits enforcement, document expected vs actual behavior; retry with Calico kind config.

**Stretch:** Default deny all ingress+egress for namespace; whitelist DNS + required paths only.

---

## 8. DevOps connections

- **Zero trust:** NetworkPolicy is baseline; service mesh adds L7 policy.
- **Debugging:** Silent drops — use flow logs (Cilium Hubble, Calico flow logs).
- **Multi-tenant:** Namespace isolation + NP per tenant.

---

## Quick reference

| Task | Command |
|------|---------|
| List NP | `kubectl get networkpolicy -n NS` |
| Test | netshoot pod + curl/nc |
| Select all pods | `podSelector: {}` |
| DNS egress | Allow UDP/TCP 53 to kube-dns |

**Next:** [Day 16 — PersistentVolumes & PVCs](../day16/)
