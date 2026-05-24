# Day 3 — State, Remote Backends, Import & Drift

**Goal:** Understand Terraform state, configure a production-style S3 + DynamoDB remote backend, use state subcommands safely, import existing resources, and detect drift.

**Time:** 5–6 hours

---

## 1. What is state?

Terraform **state** maps your HCL addresses (`aws_s3_bucket.lab`) to real cloud IDs (`my-bucket-abc123`).

```
  Configuration (.tf)     State (.tfstate)        Real world (AWS)
  aws_s3_bucket.lab  <->  bucket = "my-bucket" <->  actual bucket
```

Without state, Terraform cannot know what it already created.

| Property | Implication |
|----------|-------------|
| State is **required** | Back it up; protect it |
| State may contain **secrets** | Encrypt at rest; restrict IAM |
| State is **not** a secret store | Use Secrets Manager for credentials |

**DevOps note:** Teams use **remote state** with locking so two engineers (or CI jobs) never apply concurrently.

---

## 2. Local vs remote state

| Local (default) | Remote (S3, Terraform Cloud, etc.) |
|-----------------|-------------------------------------|
| `terraform.tfstate` on disk | Stored in shared backend |
| No locking | DynamoDB or native locking |
| Fine for solo labs | Required for teams |

---

## 3. Bootstrap remote backend (AWS)

**Chicken-and-egg:** The backend bucket must exist before you can use it. Two approaches:

1. **Bootstrap stack** — separate minimal Terraform (or CLI) creates bucket + lock table once.
2. **Existing bucket** — use an org-wide state bucket created by platform team.

### Bootstrap resources (one-time)

```hcl
# bootstrap/main.tf — apply once, then use outputs in other projects
resource "aws_s3_bucket" "terraform_state" {
  bucket = "devops-handbook-tfstate-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_dynamodb_table" "terraform_lock" {
  name         = "devops-handbook-tflock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
```

### Backend block in workload project

```hcl
terraform {
  backend "s3" {
    bucket         = "devops-handbook-tfstate-123456789012"
    key            = "day3/lab/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "devops-handbook-tflock"
    encrypt        = true
  }
}
```

After adding `backend`, run:

```bash
terraform init -migrate-state   # moves local state to S3
```

---

## 4. State subcommands

```bash
terraform state list
terraform state show aws_s3_bucket.lab
terraform state mv aws_s3_bucket.old aws_s3_bucket.new
terraform state rm aws_s3_bucket.orphan   # removes from state only — does NOT delete AWS resource
```

| Command | Effect |
|---------|--------|
| `state rm` | Stop managing resource; leaves cloud object |
| `state mv` | Rename address (refactors) |
| `state pull` / `push` | Advanced — avoid manual push in prod |

Terraform 1.1+ **`moved` block** (preferred for renames):

```hcl
moved {
  from = aws_s3_bucket.old
  to   = aws_s3_bucket.new
}
```

---

## 5. Import existing resources

Bring console-created resources under Terraform management.

### CLI import (classic)

```bash
terraform import aws_s3_bucket.imported my-existing-bucket-name
terraform plan   # align config with reality
```

### Import block (Terraform 1.5+)

```hcl
import {
  to = aws_s3_bucket.imported
  id = "my-existing-bucket-name"
}

resource "aws_s3_bucket" "imported" {
  bucket = "my-existing-bucket-name"
  # ... matching attributes
}
```

```bash
terraform plan -generate-config-out=generated.tf   # optional helper
terraform apply
```

---

## 6. Drift detection

**Drift** = difference between state/config and actual infrastructure.

```bash
terraform plan          # shows drift as unexpected changes
terraform apply -refresh-only   # update state from real world without changes
```

Someone changed a tag in the console? Plan shows `~` on tags. Options:

1. Re-apply Terraform (restore desired state).
2. Update `.tf` to match intentional console change.
3. Use IAM/policies to deny manual changes (SCPs, IAM boundary).

**DevOps note:** Scheduled `terraform plan` in CI (no apply) detects drift early.

---

## 7. State locking

When DynamoDB lock is configured:

```
Error: Error acquiring the state lock
```

Another `apply` is running. If a job crashed:

```bash
terraform force-unlock LOCK_ID   # only when sure no other apply is active
```

Never force-unlock blindly in production.

---

## 8. Lab — Remote state end-to-end

1. Apply bootstrap: [labs/day3-bootstrap](./labs/day3-bootstrap/)
2. Configure backend in: [labs/day3-remote-workload](./labs/day3-remote-workload/)

```bash
# Step 1 — bootstrap (local state is OK here)
cd labs/day3-bootstrap
terraform init && terraform apply
terraform output -json > /tmp/tf-backend.json

# Step 2 — workload with remote backend
cd ../day3-remote-workload
# Edit backend.tf with bucket name from bootstrap output
terraform init -migrate-state
terraform apply
terraform state list

# Step 3 — simulate drift: change a tag in AWS console, then:
terraform plan

terraform destroy
cd ../day3-bootstrap && terraform destroy   # last: only if no other projects use backend
```

**Success criteria:** State file appears in S3; second terminal `apply` blocks with lock error; drift visible in plan.

---

## 9. Key takeaways

- State is the mapping layer — treat it as production data.
- Remote backend + locking is mandatory for teams.
- Import brings legacy infra under IaC; `moved` handles refactors.
- Drift happens — detect with plan, prevent with policy and discipline.

**Previous:** [Day 2 — Variables & outputs](../day2/) · **Next:** [Day 4 — Modules](../day4/)
