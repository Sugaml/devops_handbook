# GCP for DevOps — Week 1 Handbook (Days 1–7)

A practical, CLI-first path from Google Cloud account setup to production-grade identity and automation patterns. Each day combines **service concepts**, **copy-paste commands**, and a **hands-on lab** you run in a personal sandbox project.

## Structure — Week 1: Foundations & identity

| Day | Topic | Services | Folder |
|-----|--------|----------|--------|
| 1 | Projects, regions, gcloud install & auth | Resource Manager, IAM (intro) | [day1](./day1/) |
| 2 | IAM members, roles, service accounts | Cloud IAM | [day2](./day2/) |
| 3 | Compute Engine VMs, disks, SSH | Compute Engine | [day3](./day3/) |
| 4 | VPC networks, subnets, firewall rules | VPC, Compute Engine | [day4](./day4/) |
| 5 | Cloud Storage buckets, objects, versioning | Cloud Storage | [day5](./day5/) |
| 6 | Output formats, filters, pagination, scripting | gcloud (all) | [day6](./day6/) |
| 7 | ADC, configurations, CI credentials, automation | IAM, STS | [day7](./day7/) |

## Prerequisites

- Comfort with Linux shell ([Linux handbook](../linux/README.md) Day 1–3 recommended).
- A **Google account** and billing enabled on a personal GCP project (Free Trial or $300 credits).
- **Never** use Owner credentials in CI; use service accounts with least privilege (Day 2, Day 7).

## How to use this handbook

1. Complete **Day 1** setup (`gcloud` CLI, default project, region/zone) before anything else.
2. Run every command in your own project; use `--dry-run` or preview flags where available.
3. Finish each day's **Lab** and run **teardown** commands — VMs, disks, and NAT incur hourly charges.
4. Keep a personal cheat sheet of `gcloud` filters and `--format` templates you reuse.
5. Optional: enable **Billing → Budgets & alerts** on day one to catch runaway spend.

## Recommended lab setup

```bash
# Install Google Cloud CLI (macOS)
brew install --cask google-cloud-sdk

# Linux (Debian/Ubuntu) — official apt repo
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
  | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list
sudo apt-get update && sudo apt-get install -y google-cloud-cli

# Verify
gcloud version
gcloud auth login
gcloud auth list

# Helpers used throughout
brew install jq   # macOS
sudo apt install -y jq  # Debian/Ubuntu

# Shell ergonomics
export CLOUDSDK_CORE_DISABLE_PROMPTS=1   # scripts: no interactive prompts
```

### Safe lab defaults

```bash
export GCP_PROJECT=devops-handbook-lab    # replace with your project ID
export GCP_REGION=us-central1
export GCP_ZONE=us-central1-a

gcloud config set project "$GCP_PROJECT"
gcloud config set compute/region "$GCP_REGION"
gcloud config set compute/zone "$GCP_ZONE"

# Label everything you create (GCP uses labels, not AWS-style tags)
export LAB_LABELS="env=lab,project=devops-handbook"
```

## Cost & safety

| Resource | Cost note |
|----------|-----------|
| Compute Engine VM (`e2-micro`) | Free tier eligible in select regions — still **delete after labs** |
| Persistent disk | Charged while disk exists, even if VM stopped |
| Cloud NAT | ~$0.045/hr + data — only enable when taught; deleteSelected for Week 2** |
| External IP (static) | Small hourly charge if unattached |
| Cloud Storage | Pennies for lab buckets; delete buckets + objects in teardown |

Always run teardown commands in each day's lab. Set a **billing budget alert** at $5–10 for learning accounts.

## Design notes

- Commands target **gcloud** current stable channel; `gsutil` appears where still idiomatic (Day 5).
- Examples use `us-central1` / `us-central1-a`; replace with your home region/zone.
- Production callouts highlight Terraform, Workload Identity Federation, and org/folder hierarchy.
- Curriculum map and decisions: [DESIGN.md](./DESIGN.md).

## Related handbooks

- [Linux for DevOps](../linux/README.md) — shell, SSH, systemd
- [Docker for DevOps](../docker/README.md) — containers before GKE days
- [Kubernetes for DevOps](../kubernetes/README.md) — GKE builds on Day 3–4 networking
- [AWS for DevOps](../aws/README.md) — parallel cloud track for comparison

## Progress checklist

```
[ ] Day 1  [ ] Day 4  [ ] Day 7
[ ] Day 2  [ ] Day 5
[ ] Day 3  [ ] Day 6
```
