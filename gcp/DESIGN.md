# GCP Handbook — Design & curriculum notes

## Goals

- **CLI-first**: Every day is actionable from a terminal; Console steps appear only when CLI is awkward (e.g. enabling APIs first time).
- **DevOps trajectory**: Days 1–7 (identity + CLI craft + core compute/network/storage) → Week 2+ (GKE, Cloud Run, Cloud Build, Terraform, org policy) when extended.
- **Week 1 service coverage**: Resource Manager, Cloud IAM, Compute Engine, VPC, Cloud Storage, gcloud scripting, ADC / WIF patterns.

## Pedagogy

| Pattern | Usage |
|---------|--------|
| Goal + time box | Sets expectations (3–6 h/day) |
| Tables | IAM role comparison, subnet models, storage classes |
| Code blocks | Runnable `gcloud` / `gsutil` commands |
| DevOps callout | CI runners, least privilege, labels, keyless auth |
| Lab | Creates + verifies + **teardown** |
| Prev/Next links | Linear path with optional skips |

## GCP vs AWS mental model (Week 1)

| AWS | GCP | Note |
|-----|-----|------|
| Account | Project | Billing attaches to project; org/folder optional |
| Region + AZ subnet | Region + regional subnet | GCP subnets are regional, not per-AZ |
| Security group | Firewall rule (VPC) | Tag-based targeting in GCP |
| S3 | Cloud Storage (GCS) | Uniform bucket-level access default in new buckets |
| IAM role (assume) | Service account impersonation | Prefer SA over user keys |
| STS GetCallerIdentity | `gcloud auth list` + `gcloud config get-value account` | ADC separate from user creds |

## Edge cases documented in days

- **API not enabled**: Most services return `SERVICE_DISABLED` — enable with `gcloud services enable` (Day 1).
- **IAM propagation**: Role binding changes can take 60–120 seconds — retry in scripts (Day 7).
- **Default VPC**: Auto-created; labs use custom VPC from Day 4 onward for clarity.
- **OS Login vs metadata SSH keys**: Day 3 covers metadata keys; production prefers OS Login + IAM.
- **Service account keys**: Anti-pattern for prod; document keyless alternatives (Day 2, Day 7).

## Performance / cost optimizations

- **e2-micro** / **e2-small** for labs; mention **Spot VMs** (preemptible successor) on Day 3.
- **Standard** storage class for lab buckets; Nearline/Coldline only when lifecycle taught (Day 5).
- **Balanced PD** (`pd-balanced`) default for new disks; mention **pd-ssd** for IOPS workloads (Day 3).
- **Private Google Access** on subnets reduces NAT need for Google APIs (Day 4).

## User feedback / iteration

- Week 2 track: GKE, Artifact Registry, Cloud Build, Secret Manager, Cloud Monitoring.
- Optional Terraform companion referencing same resource names as CLI labs.
- Add GitHub Actions WIF lab snippet when users request CI-first flow (Day 7 seeds this).

## Versioning

- Written for Google Cloud CLI current stable and APIs as of 2025–2026; verify flags with `gcloud --help` and `gcloud cheat-sheet`.
