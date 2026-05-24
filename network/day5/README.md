# Day 5 — Firewalls, Filtering & Zero-Trust Basics

**Goal:** Understand how packets are filtered on Linux and in cloud networks, write minimal allow rules safely, and avoid locking yourself out of SSH.

**Time:** 5–7 hours (theory + hands-on — use a lab VM with console access)

---

## 1. Defense in depth

| Layer | Mechanism | Scope |
|-------|-----------|-------|
| Cloud edge | WAF, Shield, DDoS | Internet-facing apps |
| VPC | Network ACL (stateless subnet) | Subnet boundary |
| Instance | Security group / host firewall | Per VM or ENI |
| Host OS | nftables/iptables, firewalld | Process-level network stack |
| App | AuthN/Z, mTLS | HTTP/gRPC |

**Principle:** Default **deny**, explicit **allow** — document every rule with owner and ticket.

---

## 2. Stateful vs stateless filtering

| | **Stateful** | **Stateless** |
|---|--------------|---------------|
| Tracks connections | Yes (conntrack) | No |
| Return traffic | Often automatic for established | Must allow both directions explicitly |
| Examples | `iptables` ESTABLISHED, AWS SG | NACL, raw port filters |

**Established/related rule (concept):**

```bash
# nftables — accept return traffic for connections we initiated
# ct state established,related accept
```

---

## 3. Linux firewall stack (modern)

```
Application
    ↓
netfilter hooks (PREROUTING, INPUT, FORWARD, OUTPUT, POSTROUTING)
    ↓
nftables (preferred)  OR  iptables-nft compatibility
    ↓
conntrack
```

Check what your distro uses:

```bash
sudo nft list ruleset
sudo iptables -L -n -v    # may map to nft backend
which firewall-cmd ufw
```

---

## 4. nftables essentials

```bash
# View current ruleset
sudo nft list ruleset

# Minimal table (lab — flush carefully)
sudo nft add table inet filter
sudo nft add chain inet filter input { type filter hook input priority 0 \; policy drop \; }
sudo nft add rule inet filter input iif lo accept
sudo nft add rule inet filter input ct state established,related accept
sudo nft add rule inet filter input tcp dport 22 accept
# WARNING: policy drop without SSH rule = lockout
```

### Useful match criteria

| Match | Example |
|-------|---------|
| Interface | `iifname "eth0"` |
| Protocol/port | `tcp dport 443` |
| Source IP | `ip saddr 10.0.0.0/8` |
| Destination IP | `ip daddr 192.168.1.10` |

Persist rules via distro (`/etc/nftables.conf`, firewalld zones) — **never** rely on runtime-only rules in production.

---

## 5. iptables (still in the wild)

```bash
sudo iptables -L -n -v --line-numbers
sudo iptables -S

# Allow established
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
# Default policy (careful)
sudo iptables -P INPUT DROP
```

Tables: **filter** (allow/deny), **nat** (SNAT/DNAT), **mangle** (marking, TTL).

**Kubernetes:** kube-proxy programs iptables/IPVS rules — do not blindly flush node firewall without understanding CNI/kube-proxy interaction.

---

## 6. firewalld and ufw (higher level)

### firewalld (RHEL family)

```bash
sudo firewall-cmd --state
sudo firewall-cmd --list-all
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
```

### ufw (Ubuntu)

```bash
sudo ufw status verbose
sudo ufw allow 22/tcp
sudo ufw allow from 10.0.0.0/8 to any port 5432 proto tcp
sudo ufw enable    # confirm SSH allowed first
```

---

## 7. Cloud security groups (conceptual mapping)

| On-prem mental model | AWS security group |
|----------------------|-------------------|
| Stateful firewall on NIC | Yes |
| Default deny inbound | Yes (unless rule added) |
| Allow outbound usually | Often yes (restrict in regulated envs) |
| Reference other SG | `source-group` instead of CIDR |

**NACL vs SG:**

| | **Security group** | **NACL** |
|---|-------------------|----------|
| Level | ENI/instance | Subnet |
| Stateful | Yes | No |
| Deny rules | Implicit deny | Explicit deny allowed |
| Order | All rules evaluated | Numbered rule order |

**DevOps practice:** Terraform modules for SGs; one SG per app tier; no `0.0.0.0/0` on admin ports.

---

## 8. conntrack and connection limits

```bash
sudo conntrack -L | head
cat /proc/sys/net/netfilter/nf_conntrack_count
cat /proc/sys/net/netfilter/nf_conntrack_max
```

Symptoms of full table: random drops, new connections fail under load. Tune max, reduce `TIME_WAIT`, fix connection leaks in apps.

---

## 9. Safe change procedure

1. **Schedule** maintenance window or use serial console / cloud SSM.
2. **Allow SSH** (or Session Manager) before enabling default deny.
3. Apply rules in **tmp** or use `iptables-restore` test timer (`at` job to flush in 5 min).
4. Verify from **second session** before closing first.
5. **Persist** only after validation.
6. **Document** in runbook: rule, purpose, owner.

```bash
# Example safety timer (lab)
(sleep 300 && sudo nft flush ruleset) &
# If you lose access, wait 5 min for flush — adapt to your environment
```

---

## 10. Zero-trust networking (professional framing)

- **No implicit trust** inside VPC — micro-segment with SGs, NetworkPolicies, or service mesh mTLS.
- **Identity-based access** (IAM, SPIFFE) complements IP allowlists.
- **Egress control** — not just ingress; compromised pod shouldn't phone arbitrary IPs.
- **Observability** — flow logs (VPC Flow Logs, Cilium Hubble) prove what was allowed.

---

## 11. Lab — Day 5

1. List current rules: `sudo nft list ruleset` or `sudo ufw status` — note default policies.
2. On a **lab VM**, allow loopback + established + SSH + HTTP (8080 from lab section Day 3); set input policy drop; verify SSH from a **second terminal** before disconnecting.
3. Block outbound HTTPS briefly with a test rule — `curl https://example.com` fails; remove rule.
4. Draw a diagram: client in `10.0.1.0/24` → SG allows 443 → app on `10.0.2.0/24` — label stateful return path.
5. Find `nf_conntrack_max` on your host; record current count under light load.

**Stretch:** Create two SG-style rules in nftables: allow TCP 5432 only from `10.0.1.0/24` to database IP; log dropped packets to journald.

---

## 12. DevOps connections

- **CI runners:** Outbound 443 to GitHub/GitLab; inbound none from internet.
- **Kubernetes NetworkPolicy:** Declarative pod firewall — Day 7 ties in.
- **Bastion / SSM:** No SSH from `0.0.0.0/0`; break-glass documented.
- **Compliance:** PCI/SOC audits ask for rule reviews and flow log retention.

---

## Quick reference

| Task | Command |
|------|---------|
| nft ruleset | `sudo nft list ruleset` |
| iptables list | `sudo iptables -L -n -v` |
| ufw | `sudo ufw status` |
| firewalld | `sudo firewall-cmd --list-all` |
| Conntrack | `sudo conntrack -L` |

**Previous:** [Day 4 — Routing & NAT](../day4/) · **Next:** [Day 6 — Proxies, TLS & load balancing](../day6/)
