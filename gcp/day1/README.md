# Day 1 — GCP Projects, Regions & gcloud Setup

**Goal:** Understand the GCP resource hierarchy, install the Google Cloud CLI, authenticate safely, set defaults, and verify access to your project.

**Time:** 3–5 hours

**Services:** Resource Manager, Cloud IAM (intro), Service Usage

---

## 1. GCP resource hierarchy

```
Organization (optional — company.com)
    └── Folder(s) (optional — teams/envs)
            └── Project (billing + IAM boundary)
                    └── Resources (VMs, buckets, VPCs…)
```

| Concept | Scope | CLI implication |
|---------|--------|-----------------|
| **Project** | Container for resources; has unique **project ID** | `gcloud config set project PROJECT_ID` |
| **Region** | Geographic area (`us-central1`) | Regional services (subnets, GKE regional) |
| **Zone** | Isolated datacenter within region (`us-central1-a`) | Zonal resources (single VM, zonal disk) |
| **Project number** | Numeric ID (used in some APIs, SA emails) | `123456789012` |
| **Project ID** | Globally unique string you choose | `devops-handbook-lab` |

Unlike AWS, **billing is tied to a project** (or billing account linked to projects). There is no single "account ID" equivalent to AWS's 12-digit account — use **project ID** and **project number**.

**DevOps note:** CI pipelines must export `GOOGLE_CLOUD_PROJECT` or pass `--project` explicitly. Never rely on stale laptop defaults across runners.

---

## 2. Create a lab project (Console or CLI)

If you already have a project, skip to section 3.

### Console (first-time users)

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create project → name: `DevOps Handbook Lab`, ID: `devops-handbook-lab` (must be globally unique — add suffix if taken).
3. Link a billing account (Free Trial or paid).
4. Note the **Project ID** — not the display name.

### CLI (after first login)

```bash
# List projects you can access
gcloud projects list --format="table(projectId,name,projectNumber)"

# Create project (requires org/billing permissions)
export LAB_PROJECT_ID="devops-handbook-lab-$(whoami)"
gcloud projects create "$LAB_PROJECT_ID" --name="DevOps Handbook Lab"

# Link billing — replace BILLING_ACCOUNT_ID from: gcloud billing accounts list
gcloud billing accounts list
gcloud billing projects link "$LAB_PROJECT_ID" \
  --billing-account=XXXXXX-XXXXXX-XXXXXX

gcloud config set project "$LAB_PROJECT_ID"
```

---

## 3. Install Google Cloud CLI

```bash
# macOS (Homebrew)
brew install --cask google-cloud-sdk

# Linux — Debian/Ubuntu (official repo)
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
  | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list
sudo apt-get update && sudo apt-get install -y google-cloud-cli

# Verify
gcloud version
# Google Cloud SDK 5xx.x.x
```

Install **beta** and **alpha** components if you want early features (optional):

```bash
gcloud components install beta
gcloud components update
```

Shell completion:

```bash
# bash
source "$(brew --prefix google-cloud-sdk)/path.bash.inc" 2>/dev/null || true

# zsh (macOS cask install)
source "$(brew --prefix)/share/google-cloud-sdk/path.zsh.inc"
source "$(brew --prefix)/share/google-cloud-sdk/completion.zsh.inc"
```

---

## 4. Authenticate (the right way)

### Interactive user login (humans on laptops)

```bash
gcloud auth login
# Opens browser — sign in with your Google account

gcloud auth list
# Credentialed Accounts — ACTIVE account marked with *

gcloud config set account your.email@company.com
```

**Never** download JSON keys for your personal user account. Users authenticate via OAuth; machines use **service accounts** (Day 2, Day 7).

### Application Default Credentials (ADC) — preview

Local tools (Terraform, client libraries, `gcloud` SDKs) look for ADC:

```bash
gcloud auth application-default login
# Writes credentials to ~/.config/gcloud/application_default_credentials.json
```

Day 7 covers ADC for CI/CD in depth. For now: run this once on your laptop if you plan to use Terraform later in the track.

---

## 5. Configure defaults

```bash
export GCP_PROJECT="devops-handbook-lab"   # your project ID
export GCP_REGION="us-central1"
export GCP_ZONE="us-central1-a"

gcloud config set project "$GCP_PROJECT"
gcloud config set compute/region "$GCP_REGION"
gcloud config set compute/zone "$GCP_ZONE"
gcloud config set core/disable_usage_reporting true   # optional privacy preference

# View effective config
gcloud config list
gcloud config configurations list
```

Config files live in `~/.config/gcloud/`:

| File / path | Purpose |
|-------------|---------|
| `configurations/config_default` | Named configuration (project, account, region) |
| `credentials.db` | OAuth tokens (managed by gcloud) |
| `application_default_credentials.json` | ADC for libraries |

### Named configurations (dev / staging mental model)

```bash
gcloud config configurations create handbook-lab
gcloud config configurations activate handbook-lab
gcloud config set project "$GCP_PROJECT"
gcloud config set compute/region "$GCP_REGION"

# Switch later
gcloud config configurations activate default
```

---

## 6. Enable APIs & verify access

Most GCP services require the API to be enabled on the project.

```bash
# Enable core APIs for Week 1
gcloud services enable \
  compute.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  storage.googleapis.com \
  serviceusage.googleapis.com

# List enabled services
gcloud services list --enabled --format="table(NAME,TITLE)" | head -20

# Describe project
gcloud projects describe "$GCP_PROJECT" \
  --format="yaml(projectId,name,projectNumber,lifecycleState)"
```

Test IAM — who am I?

```bash
# Active user email
gcloud config get-value account

# Your roles on this project (requires resourcemanager.projects.getIamPolicy)
gcloud projects get-iam-policy "$GCP_PROJECT" \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:$(gcloud config get-value account)" \
  --format="table(bindings.role)"
```

If you created the project, you likely have `roles/owner` — acceptable for a solo lab; **not** for production or shared CI.

---

## 7. Regions and zones

```bash
# List regions
gcloud compute regions list --format="table(name,status)" | head -15

# List zones in a region
gcloud compute zones list --filter="region:us-central1" --format="table(name,status)"

# Quota check (Compute CPUs — example)
gcloud compute regions describe us-central1 \
  --format="yaml(quotas)" | grep -A2 "CPUS"
```

Pick a **home region** close to you with `UP` status. Free tier e2-micro is eligible in select US regions — confirm in [Free Tier docs](https://cloud.google.com/free/docs/free-cloud-features).

**DevOps note:** Multi-region DR and GKE regional clusters come later; Week 1 labs are single-region.

---

## 8. CLI ergonomics

```bash
export CLOUDSDK_CORE_DISABLE_PROMPTS=1
export CLOUDSDK_CORE_PROJECT="$GCP_PROJECT"

# Structured output
gcloud projects describe "$GCP_PROJECT" --format=json | jq '.projectId'

# Help system — discover any command
gcloud compute instances create --help
gcloud cheat-sheet   # local reference

# Debug HTTP (support tickets)
gcloud projects describe "$GCP_PROJECT" --verbosity=debug 2>&1 | tail -30
```

---

## 9. First resource: label-ready project metadata

Labels are key/value metadata on resources (not the same as AWS tags on everything, but similar for cost allocation).

```bash
# Project labels (org policy may restrict)
gcloud projects update "$GCP_PROJECT" --update-labels=env=lab,owner=handbook

gcloud projects describe "$GCP_PROJECT" --format="yaml(labels)"
```

---

## 10. Lab — Day 1

1. Create (or select) a billing-enabled project; record **Project ID** and **Project number**.
2. Install `gcloud`; run `gcloud auth login` and `gcloud auth list`.
3. Set configuration: project, `compute/region`, `compute/zone`.
4. Enable APIs listed in section 6.
5. Run `gcloud projects describe` and `gcloud compute regions list` — confirm no permission errors.
6. Optional: run `gcloud auth application-default login` for future Terraform labs.
7. Add exports to `~/.bashrc` or `~/.zshrc`:

```bash
export GCP_PROJECT="your-project-id"
export GCP_REGION="us-central1"
export GCP_ZONE="us-central1-a"
export CLOUDSDK_CORE_DISABLE_PROMPTS=1
```

**Success criteria:** `gcloud config list` shows correct project; enabled APIs include Compute and Storage; you are authenticated as a user (not a downloaded JSON key).

---

## 11. Key takeaways

- **Project** is the primary boundary for billing, IAM, and APIs.
- **Region** vs **zone** matters for HA and disk attachment — zonal disks stay in one zone.
- **gcloud config** separates identities and projects on one machine.
- Enable APIs before service calls; `SERVICE_DISABLED` is the most common Day 1 error.

**Next:** [Day 2 — IAM roles, service accounts & least privilege](../day2/)
