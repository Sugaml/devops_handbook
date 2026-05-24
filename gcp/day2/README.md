# Day 2 — Cloud IAM: Members, Roles & Service Accounts

**Goal:** Model identity and authorization on GCP; bind roles to users and service accounts, create custom roles, and apply least privilege for DevOps workflows.

**Time:** 4–6 hours

**Services:** Cloud IAM, IAM Service Account Credentials

---

## 1. IAM building blocks

GCP IAM uses **allow-only** policies (no explicit Deny except **deny policies** in org — out of Week 1 scope).

| Concept | Meaning |
|---------|---------|
| **Member** | Who: `user:`, `serviceAccount:`, `group:`, `domain:`, `allUsers` |
| **Role** | Collection of permissions (`compute.instances.list`) |
| **Resource** | What: project, bucket, VM, etc. — policy binds at some level in hierarchy |

**Policy binding format:**

```
role → [member1, member2, ...]
```

**Member identifier examples:**

| Type | Example |
|------|---------|
| User | `user:alice@company.com` |
| Service account | `serviceAccount:deploy@PROJECT_ID.iam.gserviceaccount.com` |
| Google Group | `group:devops@company.com` |
| Domain | `domain:company.com` |

**DevOps note:** Production pipelines run as **service accounts**, not user accounts. Humans get roles via groups; CI gets narrow SA roles + Workload Identity Federation (Day 7).

---

## 2. Role types

| Type | Example | Use |
|------|---------|-----|
| **Basic** | `roles/owner`, `roles/editor`, `roles/viewer` | Legacy broad access — avoid in prod |
| **Predefined** | `roles/compute.instanceAdmin.v1` | Google-maintained, service-specific |
| **Custom** | `roles/handbookStorageViewer` | Least privilege bundle you define |

Prefer **predefined** or **custom** over Owner/Editor.

```bash
# List predefined roles containing "storage"
gcloud iam roles list --filter="name:storage" --format="table(name,title)" | head -20

# Describe permissions in a role
gcloud iam roles describe roles/storage.objectViewer --format="yaml(includedPermissions)" | head -30
```

---

## 3. Inspect project IAM policy

```bash
export GCP_PROJECT="${GCP_PROJECT:-devops-handbook-lab}"

# Full policy (YAML)
gcloud projects get-iam-policy "$GCP_PROJECT" --format=yaml

# Table of bindings
gcloud projects get-iam-policy "$GCP_PROJECT" \
  --format="table(bindings.role,bindings.members.list():label=MEMBERS)"
```

Test a permission (requires `gcloud beta` or `gcloud iam` test commands):

```bash
# Simulate: can this SA list buckets?
gcloud storage buckets list --impersonate-service-account=SA_EMAIL 2>&1 | head -5
# (Create SA first — section 5)
```

---

## 4. Bind roles to users and groups

```bash
# Grant Viewer on project (read-only — good for observers)
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member="user:teammate@example.com" \
  --role="roles/viewer"

# Grant via group (preferred at scale)
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member="group:devops@example.com" \
  --role="roles/compute.viewer"

# Remove binding
gcloud projects remove-iam-policy-binding "$GCP_PROJECT" \
  --member="user:teammate@example.com" \
  --role="roles/viewer"
```

**Idempotency:** Running `add-iam-policy-binding` twice is safe — duplicate bindings collapse.

**Propagation delay:** Wait 60–120 seconds after changes before CI retries fail.

---

## 5. Service accounts

A service account (SA) is an identity for applications, not humans.

```bash
export SA_NAME="handbook-deploy"
export SA_EMAIL="${SA_NAME}@${GCP_PROJECT}.iam.gserviceaccount.com"

# Create SA
gcloud iam service-accounts create "$SA_NAME" \
  --display-name="Handbook deploy automation"

# List SAs
gcloud iam service-accounts list --format="table(email,displayName)"

# Describe
gcloud iam service-accounts describe "$SA_EMAIL"
```

### Grant roles to a service account

```bash
# SA can manage Compute instances (lab — still broad)
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/compute.instanceAdmin.v1"

# SA can write objects to GCS (Day 5) — scoped role
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectAdmin"
```

### Impersonation (keyless local / CI pattern)

Grant your user permission to impersonate the SA:

```bash
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --member="user:$(gcloud config get-value account)" \
  --role="roles/iam.serviceAccountTokenCreator"

# Act as SA for one command
gcloud compute instances list \
  --impersonate-service-account="$SA_EMAIL"
```

**Production default:** impersonation or Workload Identity — **not** JSON keys.

---

## 6. Service account keys (lab only — avoid in prod)

```bash
# ANTI-PATTERN for production — keys leak, don't rotate easily
gcloud iam service-accounts keys create /tmp/handbook-sa-key.json \
  --iam-account="$SA_EMAIL"

# List keys
gcloud iam service-accounts keys list --iam-account="$SA_EMAIL"

# Delete key after lab
gcloud iam service-accounts keys delete KEY_ID --iam-account="$SA_EMAIL"
rm -f /tmp/handbook-sa-key.json
```

Org policy `iam.disableServiceAccountKeyCreation` blocks keys in mature environments — design for keyless from Day 1.

---

## 7. Custom role (least privilege)

Create a role that can only list and get Compute instances:

```bash
cat > /tmp/handbook-compute-reader.yaml << 'EOF'
title: Handbook Compute Reader
description: List and view GCE instances only
stage: GA
includedPermissions:
  - compute.instances.get
  - compute.instances.list
  - compute.zones.list
  - compute.regions.list
EOF

gcloud iam roles create handbookComputeReader \
  --project="$GCP_PROJECT" \
  --file=/tmp/handbook-compute-reader.yaml

# Bind custom role
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="projects/${GCP_PROJECT}/roles/handbookComputeReader"
```

List custom roles:

```bash
gcloud iam roles list --project="$GCP_PROJECT" --format="table(name,title)"
```

---

## 8. Resource-level IAM (Cloud Storage preview)

Bucket-level bindings override project inheritance for that bucket (Day 5 deep dive):

```bash
# Conceptual — bucket must exist first
# gsutil iam ch serviceAccount:SA:objectViewer gs://BUCKET
# gcloud storage buckets add-iam-policy-binding gs://BUCKET ...
```

Principle: grant **smallest scope** — bucket role beats project `storage.objectAdmin`.

---

## 9. Conditional IAM (production teaser)

Time-bound or tag-based access:

```yaml
# Example condition (conceptual)
condition:
  title: "Business hours only"
  expression: "request.time.getHours() >= 9 && request.time.getHours() < 17"
```

```bash
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member="user:contractor@example.com" \
  --role="roles/compute.viewer" \
  --condition="expression=request.time.getHours('America/Los_Angeles')>=9&&request.time.getHours('America/Los_Angeles')<17,title=Business hours,description=Deny outside 9-5 PT"
```

Useful for contractors and break-glass access.

---

## 10. DevOps patterns

| Pattern | Implementation |
|---------|----------------|
| Human admin | Group → `roles/owner` on non-prod only |
| Read-only on-call | Group → `roles/monitoring.viewer` + `roles/logging.viewer` |
| CI deploy | SA → custom role with `compute.instances.update` + artifact push |
| Terraform | SA → `roles/editor` is lazy; prefer granular custom role per module |
| Audit | Cloud Audit Logs record `SetIamPolicy` — enable log sinks Week 2+ |

---

## 11. Lab — Day 2

1. Create service account `handbook-deploy` in your lab project.
2. Create custom role `handbookComputeReader` with list/get instance permissions.
3. Bind custom role to `handbook-deploy` SA.
4. Grant your user `roles/iam.serviceAccountTokenCreator` on that SA.
5. Run `gcloud compute instances list --impersonate-service-account=...` (empty list is OK).
6. Create a SA key in `/tmp`, verify `GOOGLE_APPLICATION_CREDENTIALS=/tmp/key.json gcloud auth activate-service-account --key-file=...` works, then **delete the key**.
7. Remove test user bindings if you added any teammates.

**Teardown (optional SA cleanup):**

```bash
# Remove project bindings first, then delete SA
gcloud projects remove-iam-policy-binding "$GCP_PROJECT" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="projects/${GCP_PROJECT}/roles/handbookComputeReader"

gcloud iam roles delete handbookComputeReader --project="$GCP_PROJECT"
gcloud iam service-accounts delete "$SA_EMAIL" --quiet
```

**Success criteria:** You can impersonate an SA without a JSON key; you understand predefined vs custom roles.

---

## 12. Key takeaways

- IAM is **member + role + resource**; policies inherit down the hierarchy.
- **Service accounts** are identities for automation — treat like production users.
- Prefer **impersonation / WIF** over SA keys.
- Custom roles document exactly what Terraform/CI needs — good for reviews.

**Previous:** [Day 1 — Projects & gcloud setup](../day1/) · **Next:** [Day 3 — Compute Engine VMs](../day3/)
