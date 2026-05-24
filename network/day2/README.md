# Day 2 — DNS: Resolution, Records & Debugging

**Goal:** Trace how a hostname becomes an IP, configure resolver behavior on Linux, and debug the DNS failures that stall deploys and break CI.

**Time:** 4–6 hours (theory + hands-on)

---

## 1. What DNS does

The **Domain Name System** maps human names to records (mostly IPs). It is a distributed database:

```
Client → Recursive resolver → Root → TLD (.com) → Authoritative NS → Answer
```

| Role | Example | Who runs it |
|------|---------|-------------|
| **Authoritative** | NS for `example.com` | Your DNS host / Route 53 zone |
| **Recursive resolver** | 8.8.8.8, 1.1.1.1, corp DNS | ISP, cloud, IT |
| **Client stub** | `/etc/resolv.conf`, systemd-resolved | Your Linux host |

**DevOps impact:** A green health check on IP can still fail on hostname if DNS or search domains are wrong.

---

## 2. Common record types

| Type | Purpose | Example |
|------|---------|---------|
| **A** | IPv4 address | `api.example.com → 203.0.113.10` |
| **AAAA** | IPv6 address | `api.example.com → 2001:db8::1` |
| **CNAME** | Alias to another name | `www → api.example.com` |
| **MX** | Mail servers | priority + hostname |
| **TXT** | Arbitrary text | SPF, DKIM, domain verification |
| **NS** | Delegates subdomain | `example.com NS ns1.provider.com` |
| **SRV** | Service location | `_https._tcp.example.com` |
| **PTR** | Reverse DNS (IP → name) | IP ownership proofs, mail |

**CNAME chains:** Avoid loops; at CDN/cloud edges, **ALIAS/ANAME** (provider-specific) often replace CNAME at apex (`example.com` root).

---

## 3. Resolution order on Linux

Typical order (glibc **nsswitch**):

1. `/etc/hosts`
2. DNS (via resolver config)
3. (Optional) LDAP, etc.

```bash
cat /etc/nsswitch.conf | grep '^hosts'
# hosts: files dns myhostname
```

```bash
# Bypass DNS — static overrides
grep -v '^#' /etc/hosts
# 127.0.1.1 myhost myhost.localdomain
```

**Kubernetes note:** CoreDNS inside the cluster is separate from node resolver — app pods use `nameserver` in their `/etc/resolv.conf` (often cluster DNS IP).

---

## 4. Resolver configuration

### systemd-resolved (Ubuntu, many modern distros)

```bash
resolvectl status
resolvectl query example.com
ls -l /etc/resolv.conf    # often symlink to stub-resolver
```

### Classic resolv.conf

```bash
cat /etc/resolv.conf
# nameserver 10.0.0.2
# search ec2.internal corp.example.com
# options ndots:5 timeout:2 attempts:2
```

| Directive | Meaning |
|-----------|---------|
| `nameserver` | Which resolver to query |
| `search` | Suffixes appended to short names |
| `domain` | Default domain (legacy) |
| `options ndots:N` | If name has fewer than N dots, try search list first |

**Gotcha:** Short name `database` with `search prod.svc.cluster.local` can become `database.prod.svc.cluster.local` — powerful in K8s, confusing on laptops.

---

## 5. Query tools

### dig (preferred for debugging)

```bash
dig example.com A +short
dig example.com AAAA +short
dig example.com MX
dig example.com NS

# Query specific resolver
dig @8.8.8.8 example.com A

# Trace delegation path
dig +trace example.com

# DNSSEC (if enabled)
dig example.com +dnssec +multi
```

### host / nslookup

```bash
host example.com
host -t MX example.com
nslookup example.com 8.8.8.8
```

### getent (uses nsswitch — matches app behavior)

```bash
getent hosts example.com
getent ahosts example.com
```

---

## 6. TTL, caching, and stale records

| Concept | Meaning |
|---------|---------|
| **TTL** | Seconds resolvers may cache the answer |
| **Negative caching** | NXDOMAIN also cached |
| **Propagation** | Old TTL still served until expiry |

```bash
dig example.com A | grep -E '^example|IN\tA|QUERY'
# Look for: ANSWER SECTION and TTL column
```

**During cutover:** Lower TTL hours before changing IPs; verify with `dig @8.8.8.8` and your corp resolver — they may differ.

---

## 7. Reverse DNS

```bash
dig -x 8.8.8.8 +short
# dns.google.

# PTR for your server's public IP — mail and compliance teams care
```

Cloud load balancers often have provider-managed PTR; document if your app depends on reverse lookups.

---

## 8. Internal DNS patterns in DevOps

| Pattern | Example |
|---------|---------|
| Service discovery | `redis.prod.svc.cluster.local` (Kubernetes) |
| Cloud private DNS | Route 53 private zones, Azure Private DNS |
| Docker embedded DNS | Container name → IP on user-defined networks |
| Split-horizon | Same name, different answer inside VPC vs public |

---

## 9. Debugging workflow

When `curl https://api.internal` fails:

1. **Does the name resolve?** `dig api.internal` and `getent hosts api.internal`
2. **Correct IP?** Compare to known good (load balancer, ingress, service Endpoints)
3. **Which resolver?** `resolvectl status`, `/etc/resolv.conf`
4. **Authoritative vs cached?** `dig @resolver` vs `dig @authoritative-ns`
5. **After IP known** — Day 3+ (port, TLS, routing)

```bash
# Time DNS separately (rough)
time dig +short slow-or-broken.example.com
```

### Common failure messages

| Symptom | Likely cause |
|---------|----------------|
| `Could not resolve host` | NXDOMAIN, no resolver, typo |
| `Temporary failure in name resolution` | Resolver down, firewall on UDP/TCP 53 |
| Intermittent wrong backend | Split DNS, stale TTL, `/etc/hosts` override |
| Works with IP, not name | DNS only issue |

---

## 10. Lab — Day 2

1. Run `dig +short example.com A` and `AAAA` — record both if present.
2. Run `dig +trace example.com` — identify the TLD and authoritative NS in the output.
3. Add a line to `/etc/hosts`: `127.0.0.1 testapp.local` — verify with `getent hosts testapp.local` and `curl -I http://testapp.local` (if you run a local web server on 80).
4. Query your system resolver vs Google: `dig example.com` and `dig @8.8.8.8 example.com` — same TTL/answer?
5. Find your `search` domain list and explain what happens when you `ping database` (use a fake name and observe).

**Stretch:** Install `dnsmasq` in a container or VM as a caching forwarder; point a test client at it and observe TTL caching with repeated `dig`.

---

## 11. DevOps connections

- **CI/CD:** Runners must resolve internal artifact registries (`npm.corp.com`, `harbor.internal`).
- **TLS certificates:** SANs must match DNS names clients use — not the internal-only name if clients hit public URL.
- **Ingress / Route 53:** A/ALIAS/CNAME to load balancer; health checks tied to DNS failover.
- **ExternalDNS / cert-manager:** Automate records from Kubernetes Ingress — mistakes show up as DNS first.

---

## Quick reference

| Task | Command |
|------|---------|
| Quick A record | `dig +short NAME A` |
| Full answer | `dig NAME` |
| Specific resolver | `dig @IP NAME` |
| Delegation trace | `dig +trace NAME` |
| App-like lookup | `getent hosts NAME` |
| Resolver status | `resolvectl status` |

**Previous:** [Day 1 — IP addressing & interfaces](../day1/) · **Next:** [Day 3 — TCP/UDP, ports & sockets](../day3/)
