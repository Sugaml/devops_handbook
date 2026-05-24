# Day 6 — Proxies, TLS & Load Balancing

**Goal:** Understand HTTP reverse proxies, TLS termination and verification, and how load balancers distribute traffic — patterns you deploy behind every production ingress.

**Time:** 5–7 hours (theory + hands-on)

---

## 1. Forward vs reverse proxy

| | **Forward proxy** | **Reverse proxy** |
|---|-------------------|-------------------|
| Sits near | Clients (corp egress) | Servers (DMZ, edge) |
| Client knows? | Often yes (browser proxy settings) | No — client thinks it talks to origin |
| Use cases | Egress filtering, caching, compliance | TLS termination, routing, WAF, rate limit |
| Examples | Squid, corporate HTTP proxy | nginx, HAProxy, Envoy, ALB, Traefik |

```
Client → [ Reverse proxy / LB ] → App servers (pool)
              ↑
         public IP + cert
```

---

## 2. Load balancing algorithms

| Algorithm | Behavior | When to use |
|-----------|----------|-------------|
| **Round robin** | Rotate backends in order | Homogeneous, stateless apps |
| **Least connections** | Send to fewest active conns | Long-lived connections |
| **IP hash** | Same client IP → same backend | Sticky without cookies (fragile) |
| **Weighted** | Capacity proportion | Mixed instance sizes |
| **Random / RR with health checks** | Skip failed targets | All production LBs |

**Health checks:** TCP connect, HTTP GET `/health`, gRPC health — must match what "healthy" means for your app (DB up? cache warm?).

---

## 3. Session persistence (stickiness)

| Method | Pros | Cons |
|--------|------|------|
| Cookie insert (LB-generated) | Works behind NAT | Clients must accept cookies |
| App session cookie | App-controlled | Needs compatible LB |
| Source IP affinity | Simple | NAT pools break it; uneven load |

**DevOps preference:** Design **stateless** apps; use Redis/DB for session store instead of sticky LB when possible.

---

## 4. TLS essentials

| Term | Meaning |
|------|---------|
| **TLS** | Encrypts transport (successor to SSL) |
| **Certificate** | Binds public key to domain(s) |
| **CA** | Signs certs; clients trust CA bundle |
| **SAN** | Subject Alternative Names — all DNS names on cert |
| **SNI** | Client sends hostname during handshake — multi-tenant HTTPS on one IP |

### Handshake (simplified)

```
ClientHello (ciphers, SNI) →
ServerHello + certificate →
Key exchange →
Encrypted application data (HTTP)
```

```bash
# Inspect cert from CLI
openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null | openssl x509 -noout -subject -dates -ext subjectAltName

# Quick expiry check
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null | openssl x509 -noout -dates
```

### Termination vs passthrough

| Mode | Where TLS ends | Backend traffic |
|------|----------------|-----------------|
| **Termination** | Load balancer / ingress | Often plain HTTP to pods (in secure VPC) |
| **Passthrough** | Backend app | Encrypted end-to-end; LB routes TCP |
| **Re-encrypt** | LB terminates then new TLS to backend | Compliance, zero-trust mesh |

**Risk:** HTTP between LB and app on shared network — mitigate with NetworkPolicy, mTLS (service mesh), or re-encrypt.

---

## 5. curl and TLS debugging

```bash
curl -vI https://example.com/
curl -vk https://self-signed.local/     # -k insecure (lab only)

# Show cert chain
curl -vI https://example.com/ 2>&1 | grep -E 'subject:|issuer:|SSL connection|expire'

# Force TLS version (diagnostics)
curl --tlsv1.2 -I https://legacy-app.corp/
curl --tls-max 1.3 -I https://example.com/

# SNI to specific backend on shared IP
curl -vk --resolve api.example.com:443:203.0.113.10 https://api.example.com/
```

| Error | Common cause |
|-------|----------------|
| `SSL certificate problem` | Untrusted CA, expired, hostname mismatch |
| `wrong version number` | Speaking HTTP to HTTPS port |
| `connection reset` | Middlebox, wrong cipher, MTU |

---

## 6. nginx as reverse proxy (lab pattern)

Minimal config concepts:

```nginx
upstream api_backends {
    least_conn;
    server 127.0.0.1:8081;
    server 127.0.0.1:8082;
}

server {
    listen 443 ssl http2;
    server_name api.lab.local;

    ssl_certificate     /etc/nginx/ssl/api.lab.local.crt;
    ssl_certificate_key /etc/nginx/ssl/api.lab.local.key;

    location / {
        proxy_pass http://api_backends;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        access_log off;
        return 200 "ok\n";
        add_header Content-Type text/plain;
    }
}
```

**Headers apps trust:** Only honor `X-Forwarded-*` from known proxies; otherwise clients can spoof client IP.

---

## 7. Layer 4 vs Layer 7 load balancing

| | **L4 (TCP/UDP)** | **L7 (HTTP)** |
|---|------------------|---------------|
| Sees | IP, port | URLs, headers, cookies |
| Performance | Lower latency | More CPU, more features |
| Routing | By port | By path, host, header |
| Examples | NLB, HAProxy TCP mode | ALB, nginx HTTP, Ingress |

```bash
# HAProxy stats socket (awareness)
# balance roundrobin / leastconn in backend section
```

---

## 8. HTTP/2 and gRPC through proxies

- **HTTP/2:** Multiplexed streams on one TCP connection — proxies must support H2 end-to-end or downgrade safely.
- **gRPC:** Uses HTTP/2 — L7 proxy needs `grpc_pass` (nginx) or compatible Envoy filters; timeouts and body size differ from REST.

---

## 9. Rate limiting and WAF (edge)

| Control | Purpose |
|---------|---------|
| Rate limit | Abuse, brute force |
| WAF rules | OWASP Top 10 patterns |
| Geo block | Compliance, attack reduction |
| Bot management | Scrapers, credential stuffing |

Implement at **edge** (CloudFront, API Gateway, ingress controller) — not only in app code.

---

## 10. Lab — Day 6

1. Run `openssl s_client` against a public HTTPS site — note issuer, SAN, expiry.
2. Use `curl --resolve` to hit your own nginx or `python3 -m http.server` behind a local nginx if installed; otherwise simulate with two backends on 8081/8082 and one listener on 8080 using `socat` or nginx `upstream`.
3. Compare `curl -I http://127.0.0.1:8080` vs `https://` if TLS configured — document termination point.
4. Intentionally use wrong SNI or hostname — capture certificate mismatch error.
5. List which `X-Forwarded-*` headers your org ingress sets (check ingress controller docs or a test `echo` deployment).

**Stretch:** Generate self-signed cert with `openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 30 -nodes -subj '/CN=lab.local'`; terminate TLS with nginx; trust locally with `curl --cacert cert.pem`.

---

## 11. DevOps connections

- **Kubernetes Ingress:** Declarative L7 routing + cert-manager for Let's Encrypt.
- **AWS ALB/NLB:** Target groups, listener rules, ACM certificates.
- **GitOps:** Ingress manifest change triggers cert renewal and routing update.
- **Observability:** 502/504 often LB ↔ backend — correlate proxy access logs with app logs.

---

## Quick reference

| Task | Command |
|------|---------|
| Cert inspect | `openssl s_client -connect HOST:443 -servername HOST` |
| HTTPS headers | `curl -vI https://HOST/` |
| Test SNI routing | `curl --resolve NAME:443:IP https://NAME/` |
| Cert dates | `openssl x509 -noout -dates` |

**Previous:** [Day 5 — Firewalls](../day5/) · **Next:** [Day 7 — Cloud VPCs, K8s & runbooks](../day7/)
