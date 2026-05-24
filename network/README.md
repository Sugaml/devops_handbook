# Networking for DevOps — 7-Day Handbook

A practical path from IP addressing and DNS to production troubleshooting across Linux hosts, containers, load balancers, and cloud VPCs. Each day builds on the previous one with commands, diagrams, and labs you can run on a lab VM or laptop.

## Structure

| Day | Topic | Folder |
|-----|--------|--------|
| 1 | Models, IP addressing, subnets & interfaces | [day1](./day1/) |
| 2 | DNS — resolution, records, and debugging | [day2](./day2/) |
| 3 | Transport layer — TCP/UDP, ports & sockets | [day3](./day3/) |
| 4 | Routing, NAT, and path discovery | [day4](./day4/) |
| 5 | Firewalls, filtering, and zero-trust basics | [day5](./day5/) |
| 6 | Proxies, TLS, and load balancing | [day6](./day6/) |
| 7 | Cloud VPCs, K8s networking & incident playbooks | [day7](./day7/) |

## Prerequisites

- Basic Linux CLI ([Linux handbook](../linux/README.md) Day 1–2).
- A lab machine with root/sudo (VM, WSL2, or cloud instance).
- Optional: Docker for Day 4 namespace labs ([Docker handbook](../docker/README.md) Day 4 complements this track).

## How to use this handbook

1. Use a dedicated lab host — never experiment with firewalls or routing on production.
2. Run every command; capture output in notes for your own cheat sheet.
3. Complete each day's **Lab** before advancing.
4. On Day 7, assemble your personal **network triage runbook** from the checklist.

## Recommended lab setup

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y \
  iproute2 dnsutils net-tools curl wget tcpdump nmap \
  traceroute mtr-tiny jq bind9-host

# RHEL/Rocky/Amazon Linux
sudo dnf install -y \
  iproute bind-utils net-tools curl wget tcpdump nmap \
  traceroute mtr jq bind-utils

# Verify core tools
ip -br a
ss -tln
dig +short example.com A
```

## Design notes

- Examples use private ranges (`10.0.0.0/8`, `192.168.0.0/16`) and placeholder hostnames — replace with your lab.
- **DevOps connections** sections map each topic to CI/CD, Kubernetes, AWS/GCP/Azure, and on-call work.
- Day 5 covers both `nftables` (modern default) and `iptables` concepts because many distros and cloud docs still reference them.
- Day 7 ties concepts together; it is the bridge to the [Kubernetes handbook](../kubernetes/README.md) (Services, Ingress, NetworkPolicies) and [AWS handbook](../aws/README.md) (VPC, security groups, load balancers).
