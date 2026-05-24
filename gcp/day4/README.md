# Day 4 — VPC Networks, Subnets & Firewall Rules

**Goal:** Build a custom VPC with public and private subnets, control traffic with firewall rules and network tags, and understand Private Google Access for DevOps workloads.

**Time:** 4–6 hours

**Services:** VPC, Compute Engine (networking)

---

## 1. GCP networking vs AWS mental model

| AWS | GCP |
|-----|-----|
| VPC per region, subnets per AZ | **Subnet is regional** (spans all zones in region) |
| Security group (stateful) | **Firewall rules** (VPC-level, tag/target based) |
| NACL (stateless) | No direct equivalent — use firewall priorities |
| Default deny between SGs | **Implied allow** for egress; ingress denied unless rule allows |

Every project gets a **default VPC** with auto subnets. Labs use a **custom VPC** for clarity.

---

## 2. Create custom VPC and subnets

```bash
export GCP_PROJECT="${GCP_PROJECT:-devops-handbook-lab}"
export GCP_REGION="${GCP_REGION:-us-central1}"
export VPC_NAME="handbook-vpc"
export SUBNET_PUBLIC="handbook-public"
export SUBNET_PRIVATE="handbook-private"

gcloud compute networks create "$VPC_NAME" \
  --subnet-mode=custom \
  --bgp-routing-mode=regional

# Public-facing subnet (still private RFC1918 — "public" means has external IP route)
gcloud compute networks subnets create "$SUBNET_PUBLIC" \
  --network="$VPC_NAME" \
  --region="$GCP_REGION" \
  --range=10.10.1.0/24 \
  --enable-private-ip-google-access

# Private subnet for app tier
gcloud compute networks subnets create "$SUBNET_PRIVATE" \
  --network="$VPC_NAME" \
  --region="$GCP_REGION" \
  --range=10.10.2.0/24 \
  --enable-private-ip-google-access
```

List:

```bash
gcloud compute networks list
gcloud compute networks subnets list --network="$VPC_NAME" \
  --format="table(name,region,ipCidrRange,privateIpGoogleAccess)"
```

---

## 3. Firewall rules

Rules are **global** to the VPC but can target instances by **network tags** or **service accounts**.

### Allow SSH from your IP (lab)

```bash
MY_IP="$(curl -s ifconfig.me)/32"

gcloud compute firewall-rules create handbook-allow-ssh \
  --network="$VPC_NAME" \
  --direction=INGRESS \
  --priority=1000 \
  --action=ALLOW \
  --rules=tcp:22 \
  --source-ranges="$MY_IP" \
  --target-tags=ssh

# Allow HTTP to web tier
gcloud compute firewall-rules create handbook-allow-http \
  --network="$VPC_NAME" \
  --direction=INGRESS \
  --priority=1000 \
  --action=ALLOW \
  --rules=tcp:80,tcp:443 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server
```

### Deny all ingress (defense in depth — lower priority number = higher precedence)

GCP has no "deny all" default for ingress — you add explicit allows. Use **higher priority** (lower number) for permits, **lower priority** for broad denies if needed:

```bash
gcloud compute firewall-rules create handbook-deny-all-ingress \
  --network="$VPC_NAME" \
  --direction=INGRESS \
  --priority=65534 \
  --action=DENY \
  --rules=all \
  --source-ranges=0.0.0.0/0
# Only if you want explicit deny — usually allow rules at 1000 are enough
```

List rules:

```bash
gcloud compute firewall-rules list --filter="network:$VPC_NAME" \
  --format="table(name,direction,priority,allowed[],sourceRanges.list(),targetTags.list())"
```

**DevOps note:** Terraform `google_compute_firewall` resources should document **priority** and **target tags** — drift here causes outage incidents.

---

## 4. Launch VMs in subnets

```bash
export GCP_ZONE="${GCP_ZONE:-us-central1-a}"

# Web VM with external IP in public subnet
gcloud compute instances create handbook-web \
  --zone="$GCP_ZONE" \
  --subnet="$SUBNET_PUBLIC" \
  --machine-type=e2-micro \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --tags=http-server,ssh \
  --metadata=startup-script='#!/bin/bash
apt-get update && apt-get install -y nginx && systemctl enable --now nginx'

# App VM without external IP in private subnet
gcloud compute instances create handbook-app \
  --zone="$GCP_ZONE" \
  --subnet="$SUBNET_PRIVATE" \
  --no-address \
  --machine-type=e2-micro \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --tags=app
```

Private VM has no direct internet — reach via **IAP tunnel** (recommended):

```bash
gcloud compute firewall-rules create handbook-allow-iap-ssh \
  --network="$VPC_NAME" \
  --direction=INGRESS \
  --action=ALLOW \
  --rules=tcp:22 \
  --source-ranges=35.235.240.0/20 \
  --target-tags=ssh

gcloud compute ssh handbook-app --zone="$GCP_ZONE" --tunnel-through-iap
```

---

## 5. Cloud Router & Cloud NAT (egress for private VMs)

Private instances need NAT to reach the internet (apt, APIs):

```bash
gcloud compute routers create handbook-router \
  --network="$VPC_NAME" \
  --region="$GCP_REGION"

gcloud compute routers nats create handbook-nat \
  --router=handbook-router \
  --region="$GCP_REGION" \
  --nat-all-subnet-ip-ranges \
  --auto-allocate-nat-external-ips
```

**Cost warning:** NAT gateway bills hourly — **delete after lab** (teardown below).

Private Google Access (enabled on subnets) lets VMs reach `*.googleapis.com` **without** NAT for many APIs — still need NAT for `apt`, Docker Hub, etc.

---

## 6. Internal load balancing preview

Regional internal IPs and forwarding rules connect to MIG backends — Week 2. For Day 4, verify **internal DNS** between VMs:

```bash
# From handbook-web, ping internal IP of handbook-app
gcloud compute instances describe handbook-app --zone="$GCP_ZONE" \
  --format="get(networkInterfaces[0].networkIP)"
```

---

## 7. VPC peering & Shared VPC (production teaser)

| Pattern | Use |
|---------|-----|
| **VPC peering** | Connect two VPCs (non-transitive) |
| **Shared VPC** | Host project owns network; service projects attach workloads |
| **Hub-and-spoke** | Central connectivity via Network Connectivity Center |

Org-scale patterns — Week 4+ handbook extension.

---

## 8. Lab — Day 4

1. Create `handbook-vpc` with public (`10.10.1.0/24`) and private (`10.10.2.0/24`) subnets.
2. Add firewall: SSH from your IP to `ssh` tag; HTTP/HTTPS to `http-server` tag.
3. Create `handbook-web` (public subnet, external IP) and `handbook-app` (private, no external IP).
4. Enable IAP SSH; connect to private VM through tunnel.
5. Create Cloud NAT; from private VM run `curl -s https://ifconfig.me` — should work via NAT.
6. From web VM, `curl` private IP of app VM (install test HTTP server if desired).

**Teardown:**

```bash
gcloud compute instances delete handbook-web handbook-app --zone="$GCP_ZONE" --quiet
gcloud compute routers nats delete handbook-nat --router=handbook-router --region="$GCP_REGION" --quiet
gcloud compute routers delete handbook-router --region="$GCP_REGION" --quiet
gcloud compute firewall-rules delete handbook-allow-ssh handbook-allow-http \
  handbook-allow-iap-ssh handbook-deny-all-ingress --quiet 2>/dev/null || true
gcloud compute networks subnets delete "$SUBNET_PUBLIC" "$SUBNET_PRIVATE" --region="$GCP_REGION" --quiet
gcloud compute networks delete "$VPC_NAME" --quiet
```

**Success criteria:** Public VM serves HTTP; private VM SSH works via IAP; NAT provides outbound internet.

---

## 9. Key takeaways

- Subnets are **regional**; firewall rules are **VPC-global** with tag/SA targeting.
- **No external IP** + **IAP** is the secure admin pattern.
- **Cloud NAT** costs money — use Private Google Access to reduce API egress via NAT.
- Network tags are your **security group equivalent** — name them consistently (`role-web`, `env-lab`).

**Previous:** [Day 3 — Compute Engine](../day3/) · **Next:** [Day 5 — Cloud Storage](../day5/)
