# Day 5 — Networking, SSH & Security Basics

**Goal:** Diagnose connectivity, inspect sockets, use SSH safely, transfer files, and apply host firewall rules—essential for any DevOps engineer touching cloud VMs or bare metal.

**Time:** 6–8 hours

---

## 1. IP addressing and interfaces

```bash
ip addr show                    # or: ip a
ip link show
ip -br addr                     # brief

# Legacy (still common in scripts)
ifconfig -a                     # may need net-tools package
hostname -I

# Bring interface up/down
sudo ip link set eth0 up
sudo ip addr add 192.168.1.50/24 dev eth0

# Routes
ip route show
ip route get 8.8.8.8
sudo ip route add 10.0.0.0/8 via 192.168.1.1

# DNS resolver config
cat /etc/resolv.conf
resolvectl status               # systemd-resolved
```

---

## 2. Sockets, connections, and listening ports

Prefer `ss` over deprecated `netstat`:

```bash
ss -tuln                        # TCP/UDP listening, numeric
ss -tulnp                       # include process (needs root)
ss -tan state established       # active TCP connections
ss -s                           # summary statistics

# Find process on port
sudo ss -tlnp | grep :443
sudo lsof -iTCP:443 -sTCP:LISTEN

# Legacy
netstat -tuln
netstat -plant
```

**DevOps:** "Port already in use" → `ss -tlnp | grep :8080` before changing app config.

---

## 3. Connectivity testing

```bash
ping -c 4 8.8.8.8
ping -c 4 google.com

# TCP port check
nc -zv example.com 443
timeout 3 bash -c 'cat < /dev/null > /dev/tcp/127.0.0.1/22' && echo open

# Traceroute
traceroute 8.8.8.8
tracepath google.com
mtr -r -c 10 google.com         # report mode

# HTTP(S)
curl -I https://example.com
curl -v https://example.com     # verbose TLS + headers
curl -o /tmp/file.tar.gz https://releases.example.com/file.tar.gz
wget -qO- https://ifconfig.me    # public IP check
```

---

## 4. DNS troubleshooting

```bash
host google.com
dig google.com A +short
dig google.com MX
dig @8.8.8.8 example.com
dig +trace example.com          # full resolution path

nslookup google.com             # legacy interactive

# Reverse DNS
dig -x 8.8.8.8 +short

# systemd-resolved
resolvectl query google.com
```

**DevOps:** Misconfigured `/etc/resolv.conf` or VPC DNS breaks internal service discovery before app code is involved.

---

## 5. SSH — secure remote access

### Client usage

```bash
ssh user@host
ssh -p 2222 user@host
ssh -i ~/.ssh/deploy_key deploy@10.0.1.5

# Jump host (bastion)
ssh -J bastion.example.com user@internal.private
# or ~/.ssh/config:
# Host internal
#   HostName 10.0.1.5
#   User deploy
#   ProxyJump bastion.example.com

ssh-copy-id user@host           # install your public key on server
```

### `~/.ssh/config` example

```
Host prod-*
  User deploy
  IdentityFile ~/.ssh/prod_ed25519
  StrictHostKeyChecking accept-new

Host *
  ServerAliveInterval 60
  ServerAliveCountMax 3
```

### Key generation

```bash
ssh-keygen -t ed25519 -C "deploy@ci" -f ~/.ssh/deploy_ed25519
ssh-keygen -t rsa -b 4096 -f ~/.ssh/legacy_rsa   # only if required

chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519 ~/.ssh/config
chmod 644 ~/.ssh/id_ed25519.pub

# Agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/deploy_ed25519
ssh-add -l
```

### Server hardening (`/etc/ssh/sshd_config`)

```bash
# Recommended settings (verify before lockout)
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes
# AllowUsers deploy

sudo sshd -t                   # test config syntax
sudo systemctl reload sshd
```

**Never lock yourself out:** keep a second session open while changing SSH config.

---

## 6. File transfer

```bash
# scp
scp file.txt user@host:/remote/path/
scp -r ./localdir user@host:/remote/
scp -P 2222 user@host:/remote/file.txt .

# rsync (better for sync and resume)
rsync -avz ./build/ user@host:/var/www/app/
rsync -avz --delete ./build/ user@host:/var/www/app/   # mirror (destructive remote)
rsync -avz -e "ssh -p 2222" file user@host:
rsync -avz --progress --partial large.iso user@host:/tmp/

# Dry run
rsync -avzn --delete ./build/ user@host:/var/www/app/
```

**DevOps:** Ansible uses SSH; rsync patterns appear in deploy scripts and backup jobs.

---

## 7. Firewalls

### firewalld (RHEL family)

```bash
sudo systemctl status firewalld
sudo firewall-cmd --state
sudo firewall-cmd --list-all
sudo firewall-cmd --get-active-zones

sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload

sudo firewall-cmd --permanent --remove-port=8080/tcp
```

### ufw (Debian/Ubuntu)

```bash
sudo ufw status verbose
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw enable
sudo ufw delete allow 80/tcp
sudo ufw reset
```

### nftables/iptables (under the hood)

```bash
sudo nft list ruleset
sudo iptables -L -n -v              # legacy tables view
```

Cloud security groups often replace host firewalls for public services; host firewall still matters for east-west traffic and defense in depth.

---

## 8. TLS and certificates with OpenSSL

```bash
# Inspect remote cert
openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null | \
  openssl x509 -noout -subject -dates -issuer

# Inspect local file
openssl x509 -in cert.pem -text -noout

# Generate self-signed (lab only)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
  -subj "/CN=localhost"

# Check private key matches cert
openssl x509 -noout -modulus -in cert.pem | openssl md5
openssl rsa -noout -modulus -in key.pem | openssl md5
```

---

## 9. Network capture (read-only troubleshooting)

```bash
# Requires privileges; use sparingly in prod (PII/secrets in payloads)
sudo tcpdump -i any port 443 -c 20
sudo tcpdump -i eth0 host 10.0.1.5 and port 22 -w capture.pcap

# Analyze with tshark if installed
tshark -r capture.pcap
```

---

## 10. `/etc/hosts` and local overrides

```bash
cat /etc/hosts
# 127.0.0.1 localhost
# 10.0.1.10 api.internal

# Test without DNS change
curl --resolve api.example.com:443:10.0.1.10 https://api.example.com/
```

---

## 11. Lab — Day 5

1. List all listening TCP ports and the owning processes (`ss -tlnp`).
2. Trace route to a public host; note first hop (often gateway).
3. Generate an ed25519 key pair; create a `~/.ssh/config` entry for a lab host (or localhost with `ssh -i`).
4. Use `rsync -avzn` to dry-run a directory sync to `/tmp`.
5. Inspect HTTPS cert expiry for a site with `openssl s_client`.

**Stretch:** Add a ufw or firewalld rule for a custom port; verify with `nc -zv localhost PORT`.

---

## 12. DevOps connections

- **CI/CD:** Deploy keys and `ssh-agent` in pipelines; never embed private keys in repos.
- **Kubernetes:** `kubectl port-forward` tunnels; node debugging uses SSH to workers.
- **Zero trust:** SSH certificates (Vault, Teleport) scale better than static keys—Day 5 keys are the foundation.

---

## Quick reference

| Task | Command |
|------|---------|
| Interfaces | `ip a` |
| Listening ports | `ss -tlnp` |
| DNS lookup | `dig +short` |
| SSH with key | `ssh -i KEY user@host` |
| Sync files | `rsync -avz` |
| Test HTTP | `curl -Iv` |
| Cert expiry | `openssl s_client -connect host:443` |

**Previous:** [Day 4](../day4/) · **Next:** [Day 6 — Storage & backups](../day6/)
