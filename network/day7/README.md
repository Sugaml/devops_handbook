# Day 7 — Cloud VPCs, Kubernetes Networking & Production Runbooks

**Goal:** Synthesize the week into cloud and cluster mental models, then build a repeatable **network triage runbook** you can use on call.

**Time:** 6–8 hours (reading + capstone lab + runbook writing)

---

## 1. VPC anatomy (AWS-flavored; maps to GCP/Azure)

```
┌──────────────────────────────── VPC 10.0.0.0/16 ────────────────────────────────┐
│  ┌──────────────────── Public subnet 10.0.1.0/24 ──────────────────────────────┐  │
│  │  Internet Gateway ← 0.0.0.0/0                                              │  │
│  │  ALB, NAT Gateway (sometimes here), bastion (avoid)                        │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────── Private subnet 10.0.2.0/24 ────────────────────────────┐  │
│  │  App servers, EKS nodes — default route 0.0.0.0/0 → NAT Gateway           │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────── Data subnet 10.0.3.0/24 ────────────────────────────────┐  │
│  │  RDS, ElastiCache — no internet route                                       │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

| Component | Role |
|-----------|------|
| **VPC** | Isolated virtual network |
| **Subnet** | AZ-scoped IP range |
| **Route table** | Per-subnet forwarding rules |
| **IGW** | Public internet for public subnets |
| **NAT GW** | Outbound-only internet for private subnets |
| **SG / NACL** | Day 5 — filter traffic |
| **VPC endpoints** | Private access to AWS APIs (S3, ECR) without NAT |

**Design checklist:**

- Non-overlapping CIDR with on-prem and other VPCs.
- Three-tier subnets (public / private / data) minimum for production.
- One NAT GW per AZ for HA (cost vs availability tradeoff).

See [AWS handbook](../../aws/README.md) Week 2 for CLI depth on VPC and load balancers.

---

## 2. Hybrid connectivity (awareness)

| Method | Use case |
|--------|----------|
| **Site-to-Site VPN** | Quick hybrid, limited bandwidth |
| **Direct Connect / ExpressRoute** | Stable, high throughput |
| **Transit Gateway** | Hub-and-spoke many VPCs |
| **Peering** | VPC-to-VPC private routing (non-transitive) |

**Debugging:** BGP status, route propagation, overlapping CIDR, asymmetric routing (Day 4).

---

## 3. Kubernetes networking map

```
Internet
   ↓
[ Cloud LB / Ingress controller ]
   ↓
Service (ClusterIP / NodePort / LoadBalancer)
   ↓
kube-proxy OR eBPF dataplane (iptables/IPVS/Cilium)
   ↓
Pod IP (CNI-assigned from Pod CIDR)
```

| Object | What it provides |
|--------|------------------|
| **Pod** | One IP per pod (shared network namespace) |
| **Service ClusterIP** | Stable virtual IP → Endpoints (pod IPs) |
| **DNS (CoreDNS)** | `my-svc.my-ns.svc.cluster.local` |
| **Ingress** | L7 HTTP routing + TLS |
| **NetworkPolicy** | Pod-level firewall (if CNI supports it) |
| **CNI** | Calico, Cilium, Flannel, AWS VPC CNI — assigns routes/interfaces |

### Commands every DevOps engineer uses

```bash
kubectl get svc,endpoints -n app
kubectl describe svc api -n app
kubectl get pods -n app -o wide
kubectl exec -it deploy/api -- curl -sS http://other-svc.other-ns:8080/health
kubectl run tmp --rm -it --image=curlimages/curl -- curl -v http://api.app.svc:8080

# DNS from inside cluster
kubectl run dns-test --rm -it --image=busybox:1.36 -- nslookup kubernetes.default
```

### Common failure modes

| Symptom | Check |
|---------|-------|
| `Connection refused` | Service port vs `containerPort`; process listening `0.0.0.0` |
| `Connection timed out` | NetworkPolicy, SG, wrong selector on Service |
| DNS NXDOMAIN | Service name/namespace; CoreDNS pods |
| Works by IP not name | CoreDNS, `ndots`, search path |
| Ingress 502 | Backend pods not ready; wrong `targetPort` |
| Works in cluster, not from outside | LB, Ingress, firewall, TLS |

See [Kubernetes handbook](../../kubernetes/README.md) Days 6–7 and 15 for Services, Ingress, and NetworkPolicies.

---

## 4. Docker networking (bridge to K8s)

| Mode | Scope |
|------|-------|
| **bridge** | Default; NAT to host |
| **host** | Shares host network namespace |
| **overlay** | Multi-host (Swarm/K8s uses CNI instead) |
| **user-defined bridge** | Embedded DNS between containers |

```bash
docker network ls
docker network inspect bridge
docker run --rm --network mynet alpine ping -c 2 other-container
```

[Docker handbook](../../docker/README.md) Day 4 complements container DNS and bridge design.

---

## 5. Observability for network incidents

| Signal | Tool |
|--------|------|
| Flow metadata | VPC Flow Logs, Cilium Hubble |
| SYN/failure rate | LB metrics, `ss -s` on nodes |
| DNS latency | CoreDNS metrics, `dig` from clients |
| TLS expiry | cert-manager, Prometheus `ssl_exporter`, ACM |
| Path MTU | `tracepath`, synthetic checks |
| Packet capture | `tcpdump` on node (last resort, sensitive) |

**Correlation:** Align timestamps (UTC), request ID in app logs, LB access log, and trace IDs.

---

## 6. Network triage runbook (template)

Copy this into your team wiki and customize.

### Phase 0 — Triage (2 minutes)

- [ ] What is **exact URL or host:port** failing?
- [ ] **Scope:** one user, one region, all traffic, one deployment?
- [ ] **Started when:** deploy, config change, cert renewal, ISP?
- [ ] **Error class:** timeout, refused, DNS, TLS, HTTP 5xx?

### Phase 1 — DNS (Day 2)

```bash
dig +short HOST A
dig +short HOST AAAA
getent hosts HOST
# Compare from failing client vs known-good jump host
```

### Phase 2 — Layer 3 path (Day 1, 4)

```bash
ip route get DST_IP
ping -c 3 DST_IP                    # if ICMP allowed
traceroute -n DST_IP
mtr -rwzc 30 DST_IP
```

### Phase 3 — Layer 4 port (Day 3)

```bash
nc -zv HOST PORT
curl -v --connect-timeout 5 http://HOST:PORT/
ss -tlnp | grep PORT                # on server
```

### Phase 4 — Firewall (Day 5)

- Security group / NACL / NetworkPolicy change in last deploy?
- `conntrack` table full on node?
- Recent `nftables` / `ufw` change?

### Phase 5 — Application path (Day 6)

```bash
curl -vI https://HOST/path
openssl s_client -connect HOST:443 -servername HOST </dev/null
# Check cert expiry, chain, SNI
```

### Phase 6 — Kubernetes (if applicable)

```bash
kubectl get pods,svc,endpoints -n NAMESPACE
kubectl describe pod POD -n NAMESPACE
kubectl logs deploy/APP -n NAMESPACE --tail=100
kubectl exec -it POD -n NAMESPACE -- curl -v http://SERVICE:PORT/health
```

### Escalation data to attach

- Timestamp (UTC), region/AZ, source IP/CIDR
- Full `curl -v` or browser HAR
- `dig`, `traceroute`, `ss` outputs
- Recent change ticket / deployment ID

---

## 7. Professional practices

| Practice | Why |
|----------|-----|
| **Infrastructure as Code** for VPC, SG, routes | Reviewable, reproducible |
| **Least privilege SG** | Blast radius reduction |
| **Private subnets for workloads** | No direct internet ingress |
| **VPC endpoints** | Cost, security, reliability vs NAT-only egress |
| **Document CIDR registry** | Prevents peering/VPN conflicts |
| **Game days** | Break DNS, drain LB, revoke cert in staging |
| **Certificate automation** | cert-manager, ACM — no manual 90-day scrambles |

---

## 8. Capstone lab — Day 7

Build a **mini production path** on paper or in cloud free tier:

1. **Design** a VPC diagram: 2 AZs, public + private subnets, NAT, ALB → app → RDS (no public DB).
2. **List** every SG rule as a table: direction, source, dest, port, justification.
3. **Simulate** a failure: wrong security group on app tier blocks DB port — walk through the runbook phases and write expected outputs.
4. **Kubernetes add-on:** Sketch Service + Ingress for `api.example.com` → Deployment port 8080; note where TLS terminates.
5. **Write** your personal 1-page runbook from section 6 — store in your notes repo.

**Stretch:** Deploy a kind/minikube cluster, expose an app via Ingress, break it three ways (wrong selector, NetworkPolicy deny, wrong `targetPort`) and fix each using only network debugging commands.

---

## 9. Week review — what you should know

| Day | Core skill |
|-----|------------|
| 1 | CIDR, interfaces, `ip` |
| 2 | DNS resolution, `dig`, resolver config |
| 3 | TCP/UDP, ports, `ss`, `curl`, `nc` |
| 4 | Routes, NAT, `traceroute`, namespaces |
| 5 | Firewalls, SG model, safe changes |
| 6 | TLS, reverse proxy, LB concepts |
| 7 | VPC + K8s synthesis, runbooks |

### Continue learning

- [Linux handbook](../../linux/README.md) Day 5 — SSH and host networking
- [AWS handbook](../../aws/README.md) — VPC, ELB, Route 53 weeks
- [Kubernetes handbook](../../kubernetes/README.md) — Services through NetworkPolicies
- **Certifications (optional):** AWS Solutions Architect (networking sections), CKA (Services/Ingress troubleshooting)

---

## Quick reference — on-call cheat sheet

```bash
# DNS
dig +short HOST A; getent hosts HOST

# Path
ip route get IP; traceroute -n IP

# Port
nc -zv HOST PORT; curl -v --connect-timeout 5 URL

# Listeners
ss -tlnp

# TLS
echo | openssl s_client -connect HOST:443 -servername HOST 2>/dev/null | openssl x509 -noout -dates -subject

# K8s
kubectl get pods,svc,endpoints -n NS -o wide
kubectl run dbg --rm -it --image=curlimages/curl -- curl -v http://SVC:PORT/
```

**Previous:** [Day 6 — Proxies, TLS & load balancing](../day6/)

**You completed the 7-day network track.** Keep your runbook updated after every real incident — that document is what separates intermediate from professional DevOps networking.
