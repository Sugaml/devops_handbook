# Day 4 — Routing, NAT & Path Discovery

**Goal:** Read and reason about routing tables, understand NAT and default gateways, and use traceroute/MTR to find where packets stop.

**Time:** 5–7 hours (theory + hands-on; namespace lab needs root)

---

## 1. Routing fundamentals

A **router** forwards packets between networks based on the **destination IP**. Each Linux host has its own **routing table** — it is a router only if forwarding is enabled (`ip_forward`).

```bash
ip route show
# default via 192.168.1.1 dev eth0 proto dhcp metric 100
# 10.0.0.0/8 dev eth0 scope link
# 192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.50
```

| Route type | Meaning |
|------------|---------|
| **default** | Gateway of last resort (0.0.0.0/0) |
| **connected** | Subnet directly attached to interface |
| **static** | Admin-defined next hop |
| **dynamic** | From BGP, OSPF (rare on app servers) |

### Longest prefix match

Destination `10.20.5.10` matches the most specific route:

```
10.0.0.0/8 via 10.0.0.1        # less specific
10.20.0.0/16 dev eth1            # wins if present
```

```bash
ip route get 10.20.5.10
# shows interface, source IP, and next hop
```

---

## 2. Adding and removing routes (lab)

```bash
# Static route via gateway
sudo ip route add 172.16.50.0/24 via 192.168.1.254 dev eth0

# Route out specific interface (on-link)
sudo ip route add 10.50.0.0/24 dev eth0 scope link

# Default gateway
sudo ip route replace default via 192.168.1.1 dev eth0

# Delete
sudo ip route del 172.16.50.0/24

# Policy routing (advanced) — multiple tables
ip rule list
ip route show table all
```

**Production:** Persist routes via Netplan, cloud-init, or orchestration — document why static routes exist (VPN, legacy DB network).

---

## 3. IP forwarding and NAT

### Forwarding between interfaces

```bash
cat /proc/sys/net/ipv4/ip_forward   # 0 = off, 1 = on
# Enable temporarily (lab router VM)
sudo sysctl -w net.ipv4.ip_forward=1
```

### SNAT / masquerade (private → internet)

Many home routers and cloud NAT gateways rewrite **source IP** to a public address:

```bash
# nftables masquerade example (conceptual — Day 5 details)
# iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

| Term | Meaning |
|------|---------|
| **SNAT** | Source NAT — outbound traffic gets public IP |
| **DNAT** | Destination NAT — port forward to internal server |
| **PAT/NAPT** | Many private IPs share one public IP (port mapping) |

**Cloud:** AWS Internet Gateway + public subnet route `0.0.0.0/0 → igw`; private subnet uses NAT Gateway for egress.

---

## 4. Asymmetric routing (debugging trap)

Return path must match forward path through stateful firewalls and L7 proxies. If traffic goes in via LB A and returns via LB B, **TCP can break** silently.

**Symptoms:** Works on same AZ, fails cross-AZ; intermittent RST; works with `curl` from inside VPC only.

---

## 5. Path discovery tools

### traceroute

```bash
traceroute 8.8.8.8
traceroute -n 8.8.8.8              # no DNS lookups
traceroute -T -p 443 example.com   # TCP to 443 (needs root)
```

Each hop sends probes with increasing TTL; routers reply **Time Exceeded** until destination answers.

### mtr (my traceroute — continuous)

```bash
mtr -rwzc 50 8.8.8.8               # report mode, 50 cycles
mtr 10.0.0.1                       # interactive
```

Look for **loss at one hop** that disappears next hop (often ICMP rate-limit, not real packet loss).

### tracepath (no raw sockets needed)

```bash
tracepath example.com
```

---

## 6. Network namespaces (Linux mini-lab)

Namespaces isolate interfaces, routes, and ARP — same primitive Docker and Kubernetes use.

```bash
sudo ip netns add left
sudo ip netns add right

sudo ip link add veth-left type veth peer name veth-right
sudo ip link set veth-left netns left
sudo ip link set veth-right netns right

sudo ip netns exec left ip addr add 10.100.1.1/24 dev veth-left
sudo ip netns exec right ip addr add 10.100.1.2/24 dev veth-right
sudo ip netns exec left ip link set veth-left up
sudo ip netns exec right ip link set veth-right up

sudo ip netns exec left ping -c 2 10.100.1.2
sudo ip netns exec left ip route show
```

### Namespace with default route (router VM pattern)

On a **router** namespace or host with two nets:

1. Enable `ip_forward=1`.
2. Assign IPs on both sides.
3. Add default route on client namespace via router IP.
4. SNAT/masquerade on router egress (Day 5 firewall/NAT).

This mirrors: **pod → node → NAT gateway → internet**.

---

## 7. MTU and fragmentation

```bash
ip link show eth0 | grep mtu
ping -M do -s 1472 8.8.8.8        # don't fragment; 1472+28=1500
```

| Issue | Symptom |
|-------|---------|
| MTU mismatch | SSH works, large HTTPS hangs |
| VPN overhead | Need MSS clamping or lower MTU |

**Kubernetes:** Some CNIs encapsulate (VXLAN, WireGuard) — effective MTU drops; tune or enable TCP MSS clamp.

```bash
# Path MTU discovery hint
tracepath example.com
```

---

## 8. VRF and multi-homed hosts (awareness)

Servers with multiple NICs (management + data plane) need **policy routing** so replies exit the correct interface. Cloud **ENI** secondary IPs and **source/dest check** affect routing on AWS.

```bash
ip rule add from 10.0.2.5 table 100
ip route add default via 10.0.2.1 table 100
```

---

## 9. Lab — Day 4

1. Print full routing table: `ip route show table all` — identify default gateway and connected subnets.
2. For an external IP, run `ip route get <ip>` and `traceroute -n <ip>` — compare first hop.
3. Complete the **two-namespace veth lab** in section 6; verify ping both directions.
4. Add a **static route** in one namespace to a subnet reachable only via the peer's IP as gateway (simulate router).
5. Run `mtr -rwzc 20` to a stable target — note any hop with apparent loss that clears later.

**Stretch:** Enable forwarding on the host, configure masquerade (Day 5), and give `left` namespace internet via host `eth0`.

---

## 10. DevOps connections

- **VPC route tables:** Subnet → IGW, NAT GW, peering, Transit Gateway — same logic as `ip route`.
- **Kubernetes:** Pod → veth → bridge/CNI → node routing → Service SNAT.
- **VPN / Direct Connect:** Corporate CIDR propagated into cloud route tables — overlaps break peering.
- **Egress lockdown:** Private subnets without NAT cannot reach internet — package mirrors need VPC endpoints.

---

## Quick reference

| Task | Command |
|------|---------|
| Routing table | `ip route` |
| Path for destination | `ip route get DST` |
| Add static route | `ip route add NET via GW` |
| Enable forwarding | `sysctl -w net.ipv4.ip_forward=1` |
| Trace path | `traceroute`, `mtr`, `tracepath` |
| Namespaces | `ip netns add/exec` |

**Previous:** [Day 3 — TCP/UDP & ports](../day3/) · **Next:** [Day 5 — Firewalls & filtering](../day5/)
