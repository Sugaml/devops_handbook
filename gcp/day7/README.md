# Day 7 — ADC, CI Credentials & Shell Automation

**Goal:** Wire Google Cloud authentication for local tools, CI/CD, and Terraform using Application Default Credentials, service account impersonation, and Workload Identity Federation — without long-lived JSON keys.

**Time:** 5–6 hours

**Services:** Cloud IAM, IAM Credentials, STS (Workload Identity Federation)

---

## 1. Credential types on GCP

| Credential | Used by | Lifetime |
|------------|---------|----------|
| User OAuth (`gcloud auth login`) | Humans, some CLI | Hours; refreshable |
| **ADC** (`application-default`) | Client libs, Terraform, lang SDKs | User or SA-backed |
| SA JSON key file | Legacy CI | Long-lived — **avoid** |
| **Access token** via impersonation | Scripts, short CI jobs | ~1 hour |
| **WIF** (OIDC/SAML) | GitHub Actions, GitLab, Azure DevOps | Federated; no keys |

**DevOps default:** keyless — WIF or impersonation from a secure runner.

```bash
export GCP_PROJECT="${GCP_PROJECT:-devops-handbook-lab}"
export GCP_REGION="${GCP_REGION:-us-central1}"
export SA_NAME="handbook-ci"
export SA_EMAIL="${SA_NAME}@${GCP_PROJECT}.iam.gserviceaccount.com"
```

---

## 2. Application Default Credentials (ADC)

ADC is what client libraries search for automatically.

### Local development

```bash
# User-based ADC (laptop)
gcloud auth application-default login

# Verify file exists
ls -la ~/.config/gcloud/application_default_credentials.json

# Python quick test
python3 - << 'PY'
from google.auth import default
creds, project = default()
print("project:", project)
print("creds type:", type(creds).__name__)
PY
```

### ADC with service account impersonation (better for local)

```bash
gcloud auth application-default login \
  --impersonate-service-account="$SA_EMAIL"

# Scoped to one SA — Terraform plans act as CI would
export GOOGLE_IMPERSONATE_SERVICE_ACCOUNT="$SA_EMAIL"
```

Unset when done:

```bash
gcloud auth application-default revoke
unset GOOGLE_IMPERSONATE_SERVICE_ACCOUNT
```

---

## 3. Create CI service account (least privilege)

```bash
gcloud iam service-accounts create "$SA_NAME" \
  --display-name="Handbook CI deploy"

# Example: deploy to Compute + read artifacts bucket
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/compute.instanceAdmin.v1"

gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectViewer"
```

Tighten further with custom roles (Day 2) before production.

---

## 4. Short-lived tokens with impersonation

```bash
# Your user needs roles/iam.serviceAccountTokenCreator on the SA
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --member="user:$(gcloud config get-value account)" \
  --role="roles/iam.serviceAccountTokenCreator"

# Print OAuth access token (expires ~3600s)
gcloud auth print-access-token --impersonate-service-account="$SA_EMAIL"

# Use in curl against Google APIs
TOKEN=$(gcloud auth print-access-token --impersonate-service-account="$SA_EMAIL")
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://compute.googleapis.com/compute/v1/projects/${GCP_PROJECT}/zones/${GCP_REGION}-a/instances" \
  | jq '.items[].name'
```

In CI on GCP (Cloud Build, GCE, GKE): attach SA to the resource — **no token command needed**.

---

## 5. Workload Identity Federation (GitHub Actions pattern)

Allows external OIDC identity to impersonate a GCP SA **without keys**.

### High-level steps

1. Create **workload identity pool** + **OIDC provider** (GitHub).
2. Grant `roles/iam.workloadIdentityUser` on SA to principal set.
3. CI uses `google-github-actions/auth` with `workload_identity_provider` + `service_account`.

### CLI setup (lab simulation)

```bash
export POOL_ID="handbook-pool"
export PROVIDER_ID="github"
export PROJECT_NUMBER=$(gcloud projects describe "$GCP_PROJECT" --format="value(projectNumber)")
export REPO="YOUR_GITHUB_USER/devops-handbook"   # replace

gcloud iam workload-identity-pools create "$POOL_ID" \
  --location=global \
  --display-name="Handbook pool"

gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
  --location=global \
  --workload-identity-pool="$POOL_ID" \
  --display-name="GitHub" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Allow GitHub repo to impersonate SA
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${REPO}"
```

GitHub Actions snippet (`.github/workflows/gcp.yml`):

```yaml
permissions:
  contents: read
  id-token: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/handbook-pool/providers/github
          service_account: handbook-ci@PROJECT_ID.iam.gserviceaccount.com
      - uses: google-github-actions/setup-gcloud@v2
      - run: gcloud compute instances list --filter="labels.env=lab"
```

Replace `PROJECT_NUMBER`, `PROJECT_ID`, and repo name with yours.

---

## 6. Shell automation: deploy script

```bash
#!/usr/bin/env bash
# deploy-handbook.sh — idempotent mini-deploy for learning
set -euo pipefail

PROJECT="${GOOGLE_CLOUD_PROJECT:?}"
ZONE="${GCP_ZONE:-us-central1-a}"
VM="${1:-handbook-app}"
SA="${CI_SA_EMAIL:-}"   # optional impersonation

GCLOUD=(gcloud --project="$PROJECT")
[[ -n "$SA" ]] && GCLOUD+=(--impersonate-service-account="$SA")

if "${GCLOUD[@]}" compute instances describe "$VM" --zone="$ZONE" &>/dev/null; then
  echo "Instance $VM exists — skipping create"
else
  "${GCLOUD[@]}" compute instances create "$VM" \
    --zone="$ZONE" \
    --machine-type=e2-micro \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --labels=env=lab,managed-by=handbook-script \
    --tags=ssh
  echo "Created $VM"
fi

"${GCLOUD[@]}" compute instances list --filter="name=$VM" \
  --format="table(name,status,networkInterfaces[0].accessConfigs[0].natIP:label=IP)"
```

Run:

```bash
export GOOGLE_CLOUD_PROJECT="$GCP_PROJECT"
export CI_SA_EMAIL="$SA_EMAIL"   # optional
bash deploy-handbook.sh handbook-app
```

---

## 7. Terraform provider auth (preview)

```bash
# ~/.terraformrc or provider block uses ADC automatically
export GOOGLE_CLOUD_PROJECT="$GCP_PROJECT"
export GOOGLE_REGION="$GCP_REGION"
# Optional impersonation
export GOOGLE_IMPERSONATE_SERVICE_ACCOUNT="$SA_EMAIL"

terraform init
terraform plan   # uses ADC — no keys in repo
```

Never commit `*.json` keys; use WIF in GitHub/GitLab CI for `terraform apply`.

---

## 8. Audit and rotate

```bash
# List SA keys — should be empty in keyless setup
gcloud iam service-accounts keys list --iam-account="$SA_EMAIL"

# Policy who can impersonate SA
gcloud iam service-accounts get-iam-policy "$SA_EMAIL" --format=yaml

# Recent IAM changes (audit log — requires logging viewer)
gcloud logging read 'protoPayload.methodName="SetIamPolicy"' \
  --project="$GCP_PROJECT" --limit=5 --format=json 2>/dev/null | jq '.[].protoPayload.authenticationInfo.principalEmail'
```

---

## 9. DevOps checklist (production)

| Check | Action |
|-------|--------|
| No SA keys | Org policy `iam.disableServiceAccountKeyCreation` |
| CI is WIF | GitHub/GitLab OIDC → SA |
| Humans use SSO | Google Workspace + Cloud Identity |
| Least privilege | Custom roles per pipeline |
| Break-glass | Separate SA + conditional IAM |
| Project guard | Script asserts `GOOGLE_CLOUD_PROJECT` |

---

## 10. Lab — Day 7

1. Create `handbook-ci` service account with compute admin + storage viewer (lab breadth).
2. Grant your user `serviceAccountTokenCreator` on that SA.
3. Run `gcloud auth application-default login --impersonate-service-account=...`.
4. Run Python or `curl` example using printed access token.
5. Create workload identity pool + GitHub OIDC provider (use your fork repo path).
6. Run `deploy-handbook.sh` to create labeled VM; re-run to verify idempotency.
7. Confirm **zero** SA keys exist on `handbook-ci`.
8. Tear down lab resources.

**Teardown:**

```bash
gcloud compute instances delete handbook-app --zone="${GCP_ZONE:-us-central1-a}" --quiet 2>/dev/null || true

gcloud iam service-accounts remove-iam-policy-binding "$SA_EMAIL" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${REPO}" 2>/dev/null || true

gcloud iam workload-identity-pools providers delete "$PROVIDER_ID" \
  --location=global --workload-identity-pool="$POOL_ID" --quiet 2>/dev/null || true
gcloud iam workload-identity-pools delete "$POOL_ID" \
  --location=global --quiet 2>/dev/null || true

gcloud projects remove-iam-policy-binding "$GCP_PROJECT" \
  --member="serviceAccount:${SA_EMAIL}" --role="roles/compute.instanceAdmin.v1" --quiet 2>/dev/null || true
gcloud projects remove-iam-policy-binding "$GCP_PROJECT" \
  --member="serviceAccount:${SA_EMAIL}" --role="roles/storage.objectViewer" --quiet 2>/dev/null || true

gcloud iam service-accounts delete "$SA_EMAIL" --quiet 2>/dev/null || true

gcloud auth application-default revoke 2>/dev/null || true
```

**Success criteria:** ADC works with impersonation; WIF pool exists; deploy script is idempotent; no JSON keys created.

---

## 11. Week 1 recap

| Day | You can now… |
|-----|----------------|
| 1 | Configure gcloud, project, APIs |
| 2 | Bind IAM roles, create service accounts |
| 3 | Run VMs, disks, SSH |
| 4 | Custom VPC, firewalls, IAP, NAT |
| 5 | GCS buckets, versioning, lifecycle |
| 6 | `--format`, `--filter`, bash scripts |
| 7 | ADC, WIF, CI auth patterns |

**Next track (Week 2+):** GKE, Artifact Registry, Cloud Build, Monitoring, Terraform modules.

---

## 12. Key takeaways

- **ADC** bridges CLI login and application libraries.
- **Impersonation** and **WIF** replace SA keys in modern CI.
- Scripts must **assert project** and handle **IAM retry delay**.
- Day 7 patterns are what separate hobby GCP from **professional** DevOps.

**Previous:** [Day 6 — gcloud scripting](../day6/) · **Handbook home:** [GCP Week 1](../README.md)
