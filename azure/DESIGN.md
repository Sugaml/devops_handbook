# Azure Handbook — Design & curriculum notes

## Goals

- **CLI-first**: Every day is actionable from a terminal; portal steps are mentioned only when CLI is awkward.
- **DevOps trajectory**: Days 1–2 (identity + CLI craft) → 3–4 (compute + network) → 5 (storage + IaC intro) → 6 (observability) → 7 (Bicep + CI/CD + production).
- **Service coverage**: Subscriptions, Resource Manager, Entra ID, RBAC, Compute, Disks, Virtual Network, NSG, Storage, Monitor, Log Analytics, Application Insights, Bicep, Azure DevOps Pipelines, Key Vault (intro).

## Pedagogy

| Pattern | Usage |
|---------|--------|
| Goal + time box | Sets expectations (3–6 h/day) |
| Tables | Azure vs AWS analogies, SKU comparisons |
| Code blocks | Runnable `az` and Bicep snippets |
| DevOps callout | CI runners, least privilege, tagging, managed identity |
| Lab | Creates + verifies + **teardown** |
| Prev/Next links | Linear path with optional skips |

## Azure ↔ AWS mental map (for learners coming from AWS track)

| Azure | AWS analog |
|-------|------------|
| Subscription | Account (roughly) |
| Resource group | Tagging + lifecycle bucket (not a security boundary) |
| Entra ID (tenant) | IAM Identity Center directory |
| RBAC role assignment | IAM policy attachment |
| Managed identity | Instance profile / IRSA-style workload identity |
| VNet | VPC |
| NSG | Security group |
| Storage account | S3 bucket (container ≈ prefix) |
| ARM / Bicep | CloudFormation |
| Azure DevOps | CodePipeline + CodeBuild (conceptually) |

## Edge cases documented in days

- **Regional vs global**: Resource groups are regional metadata; many resources are regional; Entra ID is tenant-global.
- **RBAC propagation delay**: Role assignments can take 1–5 minutes — retry in scripts (Day 2).
- **Default NSG rules**: Azure allows VNet inbound by default; do not assume "deny all" (Day 4).
- **Storage account naming**: Globally unique, lowercase, 3–24 chars (Day 5).
- **VM public IP + NSG**: Both must allow traffic; NSG alone is not enough if no public IP (Day 3–4).

## Performance / cost optimizations

- Use **B-series burstable** VMs for labs (`Standard_B1s`).
- **Standard SSD** disks sufficient for lab OS disks; Premium only when teaching IOPS (Day 3).
- **Log Analytics** daily cap and 30-day retention for sandboxes (Day 6).
- **Managed identity** over service principal secrets in production (Day 2, 7).

## User feedback / iteration

- Optional add-on track: **AKS** (7-day extension) when users request Kubernetes on Azure.
- Optional **Terraform azurerm** companion — Bicep is primary IaC in Day 5/7 to stay native.

## Versioning

- Written for Azure CLI 2.x and APIs as of 2025–2026; verify deprecated flags with `az <cmd> -h`.
