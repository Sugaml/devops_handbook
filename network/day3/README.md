# Day 3 — Transport Layer: TCP, UDP, Ports & Sockets

**Goal:** Understand how applications communicate over ports, interpret connection states, and use `ss`, `curl`, and `nc` to prove where a failure occurs.

**Time:** 4–6 hours (theory + hands-on)

---

## 1. TCP vs UDP

| | **TCP** | **UDP** |
|---|---------|---------|
| Connection | Connection-oriented (3-way handshake) | Connectionless |
| Reliability | Retransmits, ordering | Best-effort |
| Use cases | HTTP, SSH, databases, gRPC | DNS, DHCP, VoIP, QUIC base, metrics |
| Overhead | Higher (state per connection) | Lower |

**DevOps default:** Assume TCP for app traffic unless docs say UDP (DNS, NTP, some gaming/video, WireGuard).

---

## 2. Ports and sockets

- **Port:** 16-bit number (0–65535). Well-known: 0–1023 (privileged on Linux), registered 1024–49151, dynamic/ephemeral 49152+.
- **Socket:** IP + port + protocol (+ interface binding). A **listening socket** accepts connections; **established** pairs connect client ↔ server.

```
Client 10.0.1.5:54321  →  Server 10.0.2.10:443
       (ephemeral)              (well-known HTTPS)
```

### Common ports (memorize these)

| Port | Service |
|------|---------|
| 22 | SSH |
| 53 | DNS (TCP and UDP) |
| 80 | HTTP |
| 443 | HTTPS |
| 3306 | MySQL |
| 5432 | PostgreSQL |
| 6379 | Redis |
| 8080 | Alt HTTP / proxies |
| 9090 | Prometheus (common) |

```bash
grep -E '^(ssh|http|https)' /etc/services | head
```

---

## 3. TCP handshake and teardown

**Three-way handshake (establish):**

```
Client → SYN → Server
Client ← SYN-ACK ← Server
Client → ACK → Server
```

**Teardown:** FIN/ACK exchange (simplified — can combine with half-close).

**States you'll see in `ss`:**

| State | Meaning |
|-------|---------|
| LISTEN | Server waiting for connections |
| SYN-SENT / SYN-RECV | Handshake in progress |
| ESTAB | Active connection |
| TIME-WAIT | Recently closed; holds socket ~2MSL |
| CLOSE-WAIT | Remote closed; local app hasn't closed |
| FIN-WAIT-* | Various closing phases |

**TIME-WAIT flood** on busy proxies: tune kernel or use `SO_REUSEPORT` / connection pooling — know it exists before blaming "the network."

---

## 4. Listening and connections with `ss`

Prefer **`ss`** over legacy `netstat` (faster, clearer).

```bash
# All TCP listening sockets
ss -tln
# -t TCP, -l listening, -n numeric ports

ss -tlnp                   # include process (needs root)
ss -tunap                  # TCP + UDP, all states, processes

# Established connections to port 443
ss -tn state established '( dport = :443 )'

# Summary by state
ss -s
```

### Compare with `lsof`

```bash
sudo lsof -iTCP -sTCP:LISTEN -P -n
sudo lsof -i :8080
```

---

## 5. Testing connectivity

### ping — ICMP (layer 3, not port-aware)

```bash
ping -c 3 10.0.0.1
# Blocked ICMP ≠ dead host — test TCP next
```

### nc (netcat)

```bash
# Server (listen on 9999)
nc -l 9999

# Client (another terminal)
nc -v 127.0.0.1 9999
echo hello | nc -w 2 127.0.0.1 9999

# TCP port scan single host
nc -zv example.com 80 443
```

### curl — application layer over TCP

```bash
curl -v http://127.0.0.1:8080/
curl -vk https://example.com/          # -k skips cert verify (lab only)
curl -o /dev/null -s -w '%{http_code} time=%{time_total}\n' https://example.com

# Connect timeout vs max time
curl --connect-timeout 3 --max-time 10 http://slow-host/
```

### telnet / bash /dev/tcp (quick checks)

```bash
timeout 3 bash -c 'cat < /dev/null > /dev/tcp/127.0.0.1/22' && echo open || echo closed
```

---

## 6. Binding addresses

| Bind address | Reachable from |
|--------------|----------------|
| `127.0.0.1` | Same host only |
| `0.0.0.0` | All interfaces (IPv4 any) |
| `10.0.1.5` | Only that interface IP |
| `::` | All interfaces (IPv6) |

**Security:** Database listening on `0.0.0.0:5432` without firewall is a recurring audit finding.

```bash
ss -tln | grep 5432
```

---

## 7. UDP checks

```bash
ss -uln                    # UDP listeners
dig @127.0.0.1 example.com # DNS uses UDP first

# Send UDP datagram
echo test | nc -u -w1 127.0.0.1 53
```

UDP "open" is ambiguous — no handshake; `nc -u` may show open if ICMP port unreachable is not returned.

---

## 8. Capture packets (intro)

```bash
# Capture HTTP on port 80 (needs root)
sudo tcpdump -i any port 80 -nn -c 20

# Specific host
sudo tcpdump -i eth0 host 10.0.1.5 and port 443 -w /tmp/capture.pcap
# Analyze later: wireshark, tshark
tshark -r /tmp/capture.pcap -Y 'tcp.flags.syn==1'
```

Use captures when `ss` shows ESTAB but app errors persist — prove retransmits, RST, or TLS issues.

---

## 9. Timeouts and proxies (preview)

| curl phase | Flag / symptom |
|------------|----------------|
| DNS | `Could not resolve host` |
| TCP connect | `Connection timed out` (firewall, wrong IP, down host) |
| TCP refused | `Connection refused` (nothing listening) |
| TLS | Certificate errors after connect |

```bash
curl -v -x http://proxy.corp:8080 https://external.com
```

Day 6 covers HTTP proxies and TLS in depth.

---

## 10. Lab — Day 3

1. Run `ss -tlnp` — list three listening services and their ports (SSH, something else).
2. Start `python3 -m http.server 8765` — verify with `ss -tln | grep 8765` and `curl -I http://127.0.0.1:8765/`.
3. From another machine (or namespace), test `nc -zv <your-ip> 8765` — if blocked, note firewall for Day 5.
4. While `curl http://127.0.0.1:8765/` runs, in another window: `ss -tn state established | grep 8765`.
5. Stop the server; observe port closed: `curl` fails with **Connection refused** — contrast with blocking firewall (**timeout**).

**Stretch:** Capture SYN packets during `curl` with `sudo tcpdump -i lo port 8765 -nn`.

---

## 11. DevOps connections

- **Kubernetes readiness:** Probe hits TCP or HTTP on container port — must match `containerPort` and process bind address.
- **Load balancers:** Health checks are often TCP:443 or HTTP GET — wrong port = all targets unhealthy.
- **Security groups:** Allowlist **destination port** on target, **source** on client (see Day 5).
- **Connection draining:** Rolling deploys + `TIME-WAIT` — why brief 502s happen during scale-in.

---

## Quick reference

| Task | Command |
|------|---------|
| Listen sockets | `ss -tlnp` |
| Established | `ss -tn state established` |
| Port open test | `nc -zv HOST PORT` |
| HTTP debug | `curl -v URL` |
| Process on port | `sudo lsof -i :PORT` |

**Previous:** [Day 2 — DNS](../day2/) · **Next:** [Day 4 — Routing, NAT & path discovery](../day4/)
