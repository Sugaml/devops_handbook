# Day 1 — Network Models, IP Addressing & Interfaces

**Goal:** Speak confidently about layers, CIDR, and how a Linux host gets an IP — the vocabulary every DevOps engineer needs before touching cloud VPCs or Kubernetes CNI.

**Time:** 4–6 hours (theory + hands-on)

---

## 1. Why networking matters in DevOps

| Scenario | Networking skill you need |
|----------|---------------------------|
| App "can't reach database" | Know IP vs hostname, port, and which interface/route is used |
| CI pipeline timeout | DNS, egress firewall, proxy, TLS |
| Kubernetes Service not working | Cluster IP, kube-proxy, NetworkPolicy |
| Terraform VPC design | Subnets, route tables, NAT, security groups |
| Incident: latency spike | RTT, packet loss, connection states |

You do not need to be a network engineer — you need **systematic debugging** and correct terminology.

---

## 2. OSI vs TCP/IP (practical view)

Developers and operators usually work from the **TCP/IP model**:

| TCP/IP layer | Examples | DevOps touchpoints |
|--------------|----------|-------------------|
| **Link** | Ethernet, Wi-Fi, MAC | Switch ports, ARP, interface `eth0` |
| **Internet** | IPv4, IPv6, ICMP | IP addresses, ping, routing |
| **Transport** | TCP, UDP | Ports, load balancers, `ss` |
| **Application** | HTTP, DNS, SSH, gRPC | Ingress, API gateways, certs |

**Encapsulation mental model:** HTTP bytes → TCP segment (port 443) → IP packet (src/dst IP) → Ethernet frame (MAC addresses on the local segment).

```
[ HTTP ] → [ TCP :443 ] → [ IP 10.0.1.5 → 10.0.2.10 ] → [ Ethernet frame ]
```

When something fails, identify **which layer** first: link (interface down?), IP (no route?), transport (connection refused?), application (HTTP 502?).

---

## 3. IPv4 addressing and CIDR

An IPv4 address is **32 bits**, written as four octets: `192.168.10.25`.

### Network vs host portion

A **subnet mask** (or **prefix length**) splits the address into network and host bits.

| CIDR | Mask | Hosts (usable)* | Typical use |
|------|------|-----------------|-------------|
| `/32` | 255.255.255.255 | 1 | Loopback alias, host route |
| `/24` | 255.255.255.0 | 254 | Small subnet, Docker bridge |
| `/16` | 255.255.0.0 | 65,534 | VPC subnet in labs |
| `/8` | 255.0.0.0 | ~16M | Rare; private supernets in design docs |

\*Usable hosts exclude network and broadcast addresses on many traditional networks; cloud VPCs often treat all addresses as usable — follow your platform docs.

### Private (RFC 1918) ranges — use these in labs

| Range | CIDR |
|-------|------|
| 10.0.0.0 – 10.255.255.255 | 10.0.0.0/8 |
| 172.16.0.0 – 172.31.255.255 | 172.16.0.0/12 |
| 192.168.0.0 – 192.168.255.255 | 192.168.0.0/16 |

### Calculate networks

```bash
# Install ipcalc if available (package: ipcalc)
ipcalc 192.168.10.0/24
# Network:   192.168.10.0
# Netmask:   255.255.255.0 (/24)
# HostMin:   192.168.10.1
# HostMax:   192.168.10.254
# Broadcast: 192.168.10.255

# Python one-liner without extra tools
python3 -c "
import ipaddress
net = ipaddress.ip_network('10.20.0.0/22', strict=False)
print('network:', net.network_address)
print('broadcast:', net.broadcast_address)
print('hosts:', net.num_addresses - 2)
print('first host:', list(net.hosts())[0])
"
```

**DevOps rule:** In Terraform or cloud consoles, **never overlap** VPC CIDRs you might peer or connect via VPN.

---

## 4. IPv6 essentials (you will see this in production)

| Concept | IPv4 habit | IPv6 note |
|---------|------------|-----------|
| Address length | 32 bits | 128 bits, hex groups |
| Localhost | 127.0.0.1 | ::1 |
| Link-local | 169.254.x.x (APIPA) | fe80::/10 |
| DHCP | dhcp client | SLAAC + DHCPv6 |

```bash
ip -6 addr show
ping -6 -c 2 ipv6.google.com   # if you have v6 connectivity
```

Many clusters are **IPv4-primary** today; still document whether your org enables IPv6 on load balancers and ingress.

---

## 5. MAC addresses and ARP (link layer)

- **MAC:** 48-bit hardware (or virtual) address on a LAN segment — e.g. `52:54:00:12:34:56`.
- **ARP:** Resolves IP → MAC on the same broadcast domain.

```bash
ip link show                    # MAC per interface
ip neigh show                   # ARP/neighbor table
ping -c 1 192.168.1.1           # populate ARP
ip neigh show 192.168.1.1
```

**Symptom:** Host has IP but cannot reach gateway on same subnet — check link up, wrong VLAN, or ARP failure (`ip neigh` stuck in `FAILED`).

---

## 6. Linux network interfaces

Modern distros use **predictable interface names** (`ens33`, `eth0`, `enp0s3`) managed by **NetworkManager** or **systemd-networkd**.

```bash
# Brief interface list
ip -br link
ip -br addr

# Detailed view
ip addr show dev eth0
ip link show dev eth0

# Legacy (still seen in scripts)
ifconfig -a                     # net-tools package
```

### Loopback

```bash
ip addr show lo
ping -c 2 127.0.0.1
# Services binding 127.0.0.1 are NOT reachable from other hosts
```

### Bring interface up/down

```bash
sudo ip link set eth0 down
sudo ip link set eth0 up
# Prefer distro tools for persistent config:
# nmcli, nmtui, or /etc/netplan/*.yaml on Ubuntu
```

---

## 7. Assigning addresses (lab only)

**Temporary** assignment (lost on reboot):

```bash
sudo ip addr add 192.168.99.10/24 dev eth0
sudo ip link set eth0 up
ip -br addr show eth0
```

**Persistent** config belongs in Netplan, NetworkManager, or cloud-init — not raw `ip addr` in production playbooks without understanding your distro.

### View routing table (preview — Day 4 goes deep)

```bash
ip route show
ip route get 8.8.8.8          # which path kernel would use
```

---

## 8. Connectivity smoke tests

```bash
# Layer 3 — is host reachable?
ping -c 4 192.168.1.1
ping -c 4 -W 2 10.255.255.1   # timeout 2s per probe

# Layer 3 without ICMP (many networks block ping)
# Use TCP/UDP check tools (Day 3): nc, curl, hping3

# Check default gateway
ip route | grep default

# DNS will be Day 2; quick check:
getent hosts example.com
```

---

## 9. Lab — Day 1

1. Run `ip -br link` and `ip -br addr` — draw a table: interface, state, IPv4, MAC.
2. Pick your default route gateway IP; run `ip route get <gateway>` and explain the output.
3. Add a secondary IP on loopback: `sudo ip addr add 10.99.99.1/32 dev lo` — ping it locally, then from another VM (should fail — why?).
4. Use Python or `ipcalc` to list all usable hosts in `172.30.0.0/26` — how many are there?
5. After pinging your gateway, inspect `ip neigh show` — find the MAC for the gateway.

**Stretch:** Create two network namespaces (preview of Day 4):

```bash
sudo ip netns add ns-a
sudo ip netns add ns-b
sudo ip link add veth-a type veth peer name veth-b
sudo ip link set veth-a netns ns-a
sudo ip link set veth-b netns ns-b
sudo ip netns exec ns-a ip addr add 10.200.1.1/24 dev veth-a
sudo ip netns exec ns-b ip addr add 10.200.1.2/24 dev veth-b
sudo ip netns exec ns-a ip link set veth-a up
sudo ip netns exec ns-b ip link set veth-b up
sudo ip netns exec ns-a ping -c 2 10.200.1.2
sudo ip netns del ns-a; sudo ip netns del ns-b
```

---

## 10. DevOps connections

- **Terraform `cidrsubnet`:** Same math as Day 1 — splitting a VPC into tier subnets (public/private/data).
- **Docker bridge:** Default often `172.17.0.0/16`; custom `--bip` avoids corporate VPN overlaps.
- **Kubernetes Pod CIDR:** Each node gets a slice; overlaps with node network = hard-to-debug failures.
- **Security groups / NACLs:** Filter by IP and port (layers 3–4); they do not replace app auth (layer 7).

---

## Quick reference

| Task | Command |
|------|---------|
| Interface + IP summary | `ip -br a` |
| Link up/down | `ip link set dev X up/down` |
| Add temp IP | `ip addr add IP/prefix dev X` |
| Routing hint | `ip route get DST` |
| ARP table | `ip neigh` |
| CIDR math | `ipcalc` or `python3 -c 'import ipaddress; ...'` |

**Next:** [Day 2 — DNS resolution & debugging](../day2/)
