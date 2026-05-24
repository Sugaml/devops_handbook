# Day 5 — Cloud Storage: Buckets, Objects & Lifecycle

**Goal:** Create and secure GCS buckets, upload and manage objects, enable versioning and lifecycle rules, and use `gcloud storage` / `gsutil` from scripts and CI.

**Time:** 4–5 hours

**Services:** Cloud Storage (GCS)

---

## 1. Cloud Storage model

| Concept | Description |
|---------|-------------|
| **Bucket** | Global unique name; lives in a **location** (region or multi-region) |
| **Object** | Blob at `gs://bucket/path/to/file` |
| **Storage class** | Standard, Nearline, Coldline, Archive |
| **Uniform bucket-level access** | IAM only — no object ACLs (recommended) |

**Naming:** Bucket names are **global** across all GCP customers — use `PROJECT_ID-handbook-artifacts` pattern.

```bash
export GCP_PROJECT="${GCP_PROJECT:-devops-handbook-lab}"
export GCP_REGION="${GCP_REGION:-us-central1}"
export BUCKET="${GCP_PROJECT}-handbook-lab"
```

---

## 2. Create a bucket

```bash
gcloud storage buckets create "gs://${BUCKET}" \
  --location="$GCP_REGION" \
  --default-storage-class=STANDARD \
  --uniform-bucket-level-access \
  --public-access-prevention \
  --labels=env=lab,project=devops-handbook

# Describe
gcloud storage buckets describe "gs://${BUCKET}" --format=yaml
```

List buckets:

```bash
gcloud storage buckets list --format="table(name,location,storageClass,updated)"
```

**DevOps note:** CI artifacts bucket — enable **uniform bucket-level access** and **public access prevention** on day one.

---

## 3. Upload, download, list objects

```bash
echo "Handbook Day 5 $(date)" > /tmp/handbook.txt
echo "version 2" > /tmp/handbook-v2.txt

# Upload (gcloud storage — preferred modern CLI)
gcloud storage cp /tmp/handbook.txt "gs://${BUCKET}/docs/handbook.txt"
gcloud storage cp /tmp/handbook-v2.txt "gs://${BUCKET}/docs/handbook-v2.txt"

# Recursive upload
mkdir -p /tmp/handbook-site && echo '<h1>Lab</h1>' > /tmp/handbook-site/index.html
gcloud storage cp -r /tmp/handbook-site "gs://${BUCKET}/www/"

# List
gcloud storage ls "gs://${BUCKET}/**"
gcloud storage ls -l "gs://${BUCKET}/docs/"

# Download
gcloud storage cp "gs://${BUCKET}/docs/handbook.txt" /tmp/downloaded.txt
cat /tmp/downloaded.txt
```

### gsutil (legacy but still common)

```bash
gsutil ls gs://${BUCKET}/
gsutil cp /tmp/handbook.txt gs://${BUCKET}/legacy/handbook.txt
gsutil -m rsync -r /tmp/handbook-site gs://${BUCKET}/www-rsync/
```

`-m` parallelizes — use for large syncs in pipelines.

---

## 4. Object metadata and versioning

Enable versioning:

```bash
gcloud storage buckets update "gs://${BUCKET}" --versioning

# Overwrite object
echo "updated content" > /tmp/handbook.txt
gcloud storage cp /tmp/handbook.txt "gs://${BUCKET}/docs/handbook.txt"

# List all versions
gcloud storage ls -a "gs://${BUCKET}/docs/handbook.txt"
```

Set custom metadata:

```bash
gcloud storage objects update "gs://${BUCKET}/docs/handbook.txt" \
  --update-custom-metadata=deployed-by=handbook,env=lab
```

---

## 5. IAM on buckets

Grant service account read access (Day 2 SA or create reader):

```bash
export SA_EMAIL="handbook-deploy@${GCP_PROJECT}.iam.gserviceaccount.com"

gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectViewer"

# Test with impersonation
gcloud storage ls "gs://${BUCKET}/" \
  --impersonate-service-account="$SA_EMAIL"
```

Common roles:

| Role | Scope |
|------|-------|
| `roles/storage.objectViewer` | Read objects |
| `roles/storage.objectCreator` | Write only (no read/list) |
| `roles/storage.objectAdmin` | Full object control |
| `roles/storage.admin` | Buckets + objects |

**Least privilege:** CI publish pipeline gets `objectCreator` on one prefix via **conditions** (advanced) or separate bucket per env.

---

## 6. Signed URLs (temporary access)

```bash
# URL valid 15 minutes (requires SA with signBlob or user creds)
gcloud storage sign-url "gs://${BUCKET}/docs/handbook.txt" \
  --duration=15m \
  --http-verb=GET
```

Use for secure artifact download without making bucket public.

---

## 7. Lifecycle management

Delete old versions or transition to cheaper class:

```bash
cat > /tmp/lifecycle.json << 'EOF'
{
  "rule": [
    {
      "action": { "type": "Delete" },
      "condition": { "age": 30, "isLive": false }
    },
    {
      "action": { "type": "SetStorageClass", "storageClass": "NEARLINE" },
      "condition": { "age": 90, "matchesStorageClass": ["STANDARD"] }
    }
  ]
}
EOF

gcloud storage buckets update "gs://${BUCKET}" --lifecycle-file=/tmp/lifecycle.json
gcloud storage buckets describe "gs://${BUCKET}" --format="yaml(lifecycle_config)"
```

---

## 8. Static website hosting (optional lab)

```bash
# Make bucket objects world-readable — ONLY for static demo sites
# Prefer Cloud CDN + backend bucket in production
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member=allUsers \
  --role=roles/storage.objectViewer \
  --condition=None 2>/dev/null || true
# Remove public binding in teardown — see lab
```

Production pattern: **Cloud Load Balancing + Cloud CDN + backend bucket**, not public IAM.

---

## 9. DevOps patterns

| Use case | Pattern |
|----------|---------|
| Terraform state | Versioned bucket + locking (GCS backend) |
| CI artifacts | Per-branch prefix `gs://bucket/builds/${BRANCH}/` |
| Container images | Use **Artifact Registry** (Week 2) — not raw GCS |
| Logs archive | Sink to GCS → lifecycle to Coldline |
| Drift detection | `gcloud storage ls` vs manifest in pipeline |

---

## 10. Lab — Day 5

1. Create bucket `PROJECT_ID-handbook-lab` with uniform access and public access prevention.
2. Upload files under `docs/` and `www/`; list with `gcloud storage ls`.
3. Enable versioning; overwrite a file; list generations with `-a`.
4. Bind `storage.objectViewer` to `handbook-deploy` SA; list with impersonation.
5. Apply lifecycle JSON (30-day delete noncurrent versions).
6. Generate a signed URL and fetch with `curl`.
7. Optional: `gsutil rsync` a local directory to the bucket.

**Teardown:**

```bash
# Remove all objects first (bucket must be empty to delete)
gcloud storage rm -r "gs://${BUCKET}/**" 2>/dev/null || true
gcloud storage buckets delete "gs://${BUCKET}" --quiet
rm -f /tmp/handbook.txt /tmp/handbook-v2.txt /tmp/lifecycle.json /tmp/downloaded.txt
rm -rf /tmp/handbook-site
```

**Success criteria:** Bucket created with safe defaults; versioning and IAM work; lifecycle policy attached.

---

## 11. Key takeaways

- Bucket names are **globally unique** — prefix with project ID.
- **Uniform bucket-level access** simplifies IAM — no object ACL sprawl.
- **Versioning** protects against accidental overwrite; pair with lifecycle for cost.
- Prefer **`gcloud storage`** for new scripts; know **gsutil** for legacy pipelines.

**Previous:** [Day 4 — VPC & firewalls](../day4/) · **Next:** [Day 6 — gcloud scripting](../day6/)
