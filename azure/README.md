# Azure for DevOps — 7-Day Handbook

A practical, CLI-first path from Azure subscription setup to production-grade identity, networking, observability, and CI/CD. Each day combines **service concepts**, **copy-paste commands**, and a **hands-on lab** you run in a personal sandbox subscription.

## Structure

| Day | Topic | Services | Folder |
|-----|--------|----------|--------|
| 1 | Subscriptions, regions, CLI install & login | Subscriptions, Resource Manager | [day1](./day1/) |
| 2 | Entra ID, RBAC, service principals & managed identity | Entra ID, RBAC | [day2](./day2/) |
| 3 | Resource groups, VMs, disks & SSH access | Compute, Disks | [day3](./day3/) |
| 4 | Virtual networks, subnets, NSGs & public IPs | Virtual Network | [day4](./day4/) |
| 5 | Storage accounts, blobs & ARM/Bicep basics | Storage, Resource Manager | [day5](./day5/) |
| 6 | Azure Monitor, Log Analytics, alerts & diagnostics | Monitor, Log Analytics | [day6](./day6/) |
| 7 | Bicep deployments, Azure DevOps CI/CD & production patterns | Bicep, DevOps, Key Vault | [day7](./day7/) |

## Prerequisites

- Comfort with Linux shell ([Linux handbook](../linux/README.md) Day 1–3 recommended).
- Basic networking vocabulary ([Network handbook](../network/README.md) Day 1–2 helps before Day 4).
- A **personal Azure account** (Free Account or Visual Studio / M365 dev subscription).
- **Never** use the subscription owner account for daily CLI work; create a dedicated admin user (Day 2).

## How to use this handbook

1. Complete **Day 1** setup (Azure CLI, login, default subscription) before anything else.
2. Run every command in your own subscription; use `--dry-run` or `what-if` before destructive changes.
3. Finish each day's **Lab** and run **teardown** commands to avoid surprise charges.
4. Keep a personal cheat sheet of `az` commands and JMESPath queries you reuse.
5. Optional: track spend daily in **Cost Management + Billing** (Day 7 covers budgets).

## Recommended lab setup

```bash
# Azure CLI (macOS)
brew update && brew install azure-cli

# Linux (Debian/Ubuntu)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Verify
az version
az login

# Helpers used throughout
brew install jq   # macOS
sudo apt install -y jq  # Debian/Ubuntu

# Session defaults for scripts
export AZURE_DEFAULTS_GROUP=rg-devops-handbook
export AZURE_DEFAULTS_LOCATION=eastus
```

### Safe lab defaults

```bash
# Set after Day 1 — replace with your subscription ID
export AZURE_SUBSCRIPTION_ID=$(az account show --query id -o tsv)
export LAB_LOCATION=eastus
export LAB_RG=rg-devops-handbook
export LAB_TAG="Project=devops-handbook Owner=you Environment=lab"

# Always tag resources you create
az group create --name "$LAB_RG" --location "$LAB_LOCATION" \
  --tags Project=devops-handbook Environment=lab
```

## Cost & safety

| Resource | Cost note |
|----------|-----------|
| Standard_B1s VM | ~$0.01/hr — **delete after Day 3–4 labs** |
| Public IP (Standard) | Small hourly charge — release when not needed |
| Log Analytics workspace | Ingestion + retention — use 30-day retention for labs |
| Storage (Hot tier) | Pennies for lab data — delete account same day |
| Azure DevOps | Free tier for small teams; pipelines minutes may apply |

Always run teardown commands in each day's lab. Set a **budget alert** (Day 7).

## Design notes

- Commands target **Azure CLI 2.x** (`az <group> <command>`).
- Examples use `eastus`; replace with a region near you (`az account list-locations -o table`).
- Production callouts highlight what changes in CI/CD, Bicep/Terraform, and landing zones.
- Curriculum map and decisions: [DESIGN.md](./DESIGN.md).

## Progress checklist

```
[ ] Day 1  [ ] Day 4
[ ] Day 2  [ ] Day 5
[ ] Day 3  [ ] Day 6
[ ] Day 7 — capstone
```

## Related handbooks

| Handbook | Why it matters for Azure |
|----------|--------------------------|
| [Linux](../linux/README.md) | SSH, systemd, shell scripting for VMs and pipelines |
| [Network](../network/README.md) | CIDR, DNS, routing before VNet design (Day 4) |
| [Git](../git/README.md) | Branching and PRs for IaC and pipeline repos |
| [Docker](../docker/README.md) | Containers before AKS / Container Apps (future track) |
| [AWS](../aws/README.md) | Parallel cloud concepts — compare IAM vs RBAC, VPC vs VNet |
