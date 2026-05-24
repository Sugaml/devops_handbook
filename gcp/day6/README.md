# Day 6 — gcloud Output, Filters & Scripting

**Goal:** Master `--format`, `--filter`, projections, and bash-friendly patterns so you can build reliable DevOps scripts, one-liners, and CI steps without clicking the Console.

**Time:** 4–5 hours

**Services:** gcloud (all), Cloud SDK scripting

---

## 1. Output formats

```bash
export GCP_PROJECT="${GCP_PROJECT:-devops-handbook-lab}"

# JSON — best for jq pipelines
gcloud compute instances list --format=json | jq '.[].name'

# YAML — readable configs
gcloud projects describe "$GCP_PROJECT" --format=yaml

# Table — human terminal
gcloud compute zones list --limit=5 --format="table(name,region,status)"

# Value — single field, script-friendly (no headers)
gcloud config get-value project
gcloud projects describe "$GCP_PROJECT" --format="value(projectNumber)"

# CSV
gcloud iam service-accounts list --format="csv(email,displayName)"
```

Disable pager in scripts:

```bash
export CLOUDSDK_CORE_DISABLE_PROMPTS=1
gcloud config set core/disable_prompts true
```

---

## 2. Projections and custom columns

```bash
# Built-in projection
gcloud compute instances list --format="table(name,zone.basename(),status)"

# Custom header
gcloud compute instances list \
  --format="table[box](name:label=INSTANCE,zone:label=ZONE,status:label=STATE)"

# Nested fields
gcloud compute instances describe INSTANCE --zone=ZONE \
  --format="get(networkInterfaces[0].accessConfigs[0].natIP)"
```

**Cheat:** use `--format=json` once, pipe to `jq`, then codify the path into `--format=value(...)` for speed.

---

## 3. Filtering

Filter syntax uses **Google API filter language** (field comparisons, logical AND/OR):

```bash
# Running instances in a zone
gcloud compute instances list \
  --filter="zone:us-central1-a AND status=RUNNING"

# Name prefix
gcloud compute instances list --filter="name~'^handbook-'"

# Labels (use labels.key=value)
gcloud compute instances list --filter="labels.env=lab"

# Disks larger than 20GB
gcloud compute disks list --filter="sizeGb>20"

# Service accounts with display name
gcloud iam service-accounts list \
  --filter="displayName:Handbook"
```

Common operators: `=`, `!=`, `<`, `>`, `:` (has), `~` (regex), `AND`, `OR`, `NOT`.

**DevOps note:** Filters run **server-side** — prefer them over `grep` on full JSON for large projects.

---

## 4. Pagination and limits

```bash
# Limit page size
gcloud compute instances list --page-size=50

# Limit total results
gcloud compute instances list --limit=10

# Sort
gcloud compute instances list --sort-by=creationTimestamp
```

For full project exports, loop with `--page-token` or use **`gcloud asset search-all-resources`** (Resource Manager API) in org-scale audits.

---

## 5. Quiet, dry-run, and flags

```bash
# Suppress prompts
gcloud compute instances delete my-vm --zone=ZONE --quiet

# Some commands support --dry-run (beta services vary)
# Always test destructive ops with --quiet only in CI after review

# Return non-zero on failure — default; use set -e in scripts
set -euo pipefail
```

---

## 6. Useful bash patterns

### Wait for operation

```bash
gcloud compute instances create handbook-wait \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --async \
  --format="value(name)" > /tmp/op.txt

OP=$(cat /tmp/op.txt)
gcloud compute operations wait "$OP" --zone=us-central1-a
```

### Loop over zones / regions

```bash
for z in $(gcloud compute zones list --filter="region:us-central1" --format="value(name)"); do
  echo "=== $z ==="
  gcloud compute instances list --filter="zone:$z" --format="value(name)"
done
```

### JSON with jq — bulk delete by label

```bash
gcloud compute instances list --filter="labels.env=lab" --format=json \
  | jq -r '.[] | [.name, .zone] | @tsv' \
  | while IFS=$'\t' read -r name zone; do
      gcloud compute instances delete "$name" --zone="$zone" --quiet
    done
```

### Config guard

```bash
: "${GCP_PROJECT:?Set GCP_PROJECT}"
ACTUAL=$(gcloud config get-value project 2>/dev/null)
[[ "$ACTUAL" == "$GCP_PROJECT" ]] || { echo "Wrong project: $ACTUAL"; exit 1; }
```

---

## 7. Script template for CI

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT="${GOOGLE_CLOUD_PROJECT:-${GCP_PROJECT:-}}"
REGION="${GCP_REGION:-us-central1}"
ZONE="${GCP_ZONE:-us-central1-a}"

[[ -n "$PROJECT" ]] || { echo "PROJECT required"; exit 1; }

gcloud config set project "$PROJECT" --quiet
gcloud config set compute/region "$REGION" --quiet
gcloud config set compute/zone "$ZONE" --quiet

# Verify auth (user or SA)
gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1

echo "Deploying to project=$PROJECT region=$REGION"
# ... your steps ...
```

---

## 8. Error handling and retries

IAM propagation and API eventual consistency:

```bash
retry() {
  local n=0 max=5 delay=5
  until "$@"; do
    n=$((n + 1))
    [[ $n -ge $max ]] && return 1
    echo "Retry $n/$max in ${delay}s..." >&2
    sleep "$delay"
  done
}

retry gcloud compute instances list --filter="name=handbook-web"
```

Parse errors:

```bash
if ! out=$(gcloud storage ls "gs://nonexistent-bucket-xyz/" 2>&1); then
  echo "$out" | grep -q "404" && echo "Bucket missing — create first"
fi
```

---

## 9. Configurations and multi-env

```bash
# List configurations
gcloud config configurations list

gcloud config configurations create prod-readonly
gcloud config configurations activate prod-readonly
gcloud config set project prod-project-id
gcloud config set account oncall@company.com

# One-off override
gcloud compute instances list --project=staging-project-id
```

Map to `KUBECONFIG`-style mental model: **one configuration per environment**.

---

## 10. Essential one-liners

```bash
# All external IPs in project
gcloud compute instances list \
  --format="table(name,zone.basename(),networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP)"

# Count VMs by status
gcloud compute instances list --format="value(status)" | sort | uniq -c

# Project number (for SA emails, WIF)
gcloud projects describe "$GCP_PROJECT" --format="value(projectNumber)"

# Enabled APIs containing compute
gcloud services list --enabled --filter="name:compute" --format="value(NAME)"

# Who can edit project IAM
gcloud projects get-iam-policy "$GCP_PROJECT" \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/owner OR bindings.role:roles/editor" \
  --format="table(bindings.role,bindings.members)"
```

---

## 11. Lab — Day 6

1. List all Compute instances using `--format=table` with custom columns.
2. Write a 10-line bash script that asserts `GCP_PROJECT` matches active config.
3. Filter service accounts whose email contains `handbook`.
4. Create two VMs with label `env=lab`; use jq loop to delete only those VMs.
5. Run an async instance create and `gcloud compute operations wait`.
6. Save three reusable `--format` snippets in your personal cheat sheet.

**Optional cleanup** from lab VMs:

```bash
gcloud compute instances list --filter="labels.env=lab" --format="value(name,zone)" \
  | while read -r name zone; do
      gcloud compute instances delete "$name" --zone="$zone" --quiet
    done
```

**Success criteria:** You can extract fields without opening JSON manually; filters reduce output; scripts fail fast on wrong project.

---

## 12. Key takeaways

- **`--format=value(...)`** + **`--filter`** are the core of scriptable gcloud.
- Server-side filters beat local `grep` at scale.
- Guard **project** and **account** at the top of every pipeline.
- Use **configurations** to switch environments safely on one laptop.

**Previous:** [Day 5 — Cloud Storage](../day5/) · **Next:** [Day 7 — ADC, CI auth & automation](../day7/)
