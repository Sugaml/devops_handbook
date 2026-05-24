# Day 1 — Install Terraform, Workflow & First Resources

**Goal:** Install Terraform, understand the core workflow (`init` → `plan` → `apply` → `destroy`), read HCL syntax, and provision your first AWS resource.

**Time:** 4–5 hours

**Provider:** hashicorp/aws

---

## 1. What is Terraform?

| Manual / click-ops | Terraform (IaC) |
|--------------------|-----------------|
| Undocumented changes in console | Version-controlled `.tf` files |
| "Works on my account" | Reproducible plans across envs |
| Drift over time | State tracks desired vs actual |
| Tribal knowledge | Code review + CI plan |

Terraform is **declarative**: you describe the desired end state; the provider figures out create/update/delete steps.

```
  .tf files  +  Provider API  +  State file
       │              │                │
       └──── terraform plan ────────────┘
                    │
              terraform apply
                    │
              AWS / Azure / GCP …
```

**DevOps note:** Treat Terraform like application code — PR reviews, linting, tests, and protected applies.

---

## 2. Install and verify

```bash
# macOS (HashiCorp tap)
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Linux — see https://developer.hashicorp.com/terraform/install
terraform version
# Terraform v1.9.x on darwin_amd64 / linux_amd64

# Enable tab completion (bash)
terraform -install-autocomplete
```

Verify AWS credentials (from [AWS Day 1](../../aws/day1/)):

```bash
export AWS_PROFILE=devops-handbook
export AWS_REGION=us-east-1
aws sts get-caller-identity
```

---

## 3. Core workflow commands

| Command | Purpose |
|---------|---------|
| `terraform init` | Download providers, configure backend |
| `terraform fmt` | Format `.tf` files to canonical style |
| `terraform validate` | Syntax + internal consistency check |
| `terraform plan` | Preview changes (dry run) |
| `terraform apply` | Execute plan (creates/updates/deletes) |
| `terraform destroy` | Tear down all managed resources |
| `terraform show` | Inspect current state |

Typical session:

```bash
cd labs/day1-s3-bucket
terraform init
terraform fmt -recursive
terraform validate
terraform plan
terraform apply   # type yes, or use -auto-approve in CI only
terraform show
terraform destroy -auto-approve
```

**Golden rule:** Never `apply` without reviewing `plan` first.

---

## 4. HCL basics

HCL (HashiCorp Configuration Language) is Terraform's language.

### Blocks and arguments

```hcl
resource "aws_s3_bucket" "lab" {
  bucket = "devops-handbook-day1-${data.aws_caller_identity.current.account_id}"

  tags = {
    Project     = "devops-handbook"
    Environment = "lab"
    ManagedBy   = "terraform"
  }
}
```

| Part | Meaning |
|------|---------|
| `resource` | Block type — creates/manages infrastructure |
| `"aws_s3_bucket"` | Resource type (provider prefix + name) |
| `"lab"` | Local name — reference as `aws_s3_bucket.lab` |
| `bucket = "..."` | Argument — passed to provider API |

### Provider block

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}
```

### Data sources (read-only)

```hcl
data "aws_caller_identity" "current" {}
# Reference: data.aws_caller_identity.current.account_id
```

Data sources fetch existing info without managing lifecycle.

---

## 5. Resource addressing and dependencies

Terraform builds a **dependency graph** automatically when one resource references another:

```hcl
resource "aws_s3_bucket" "lab" {
  bucket = "my-lab-bucket-unique-name"
}

resource "aws_s3_bucket_versioning" "lab" {
  bucket = aws_s3_bucket.lab.id   # implicit dependency

  versioning_configuration {
    status = "Enabled"
  }
}
```

Explicit dependency when no reference exists:

```hcl
depends_on = [aws_s3_bucket.lab]
```

---

## 6. Files in a root module

| File | Convention |
|------|------------|
| `main.tf` | Primary resources |
| `providers.tf` | `terraform` + `provider` blocks |
| `variables.tf` | Input variables (Day 2) |
| `outputs.tf` | Exported values (Day 2) |
| `.terraform/` | Provider plugins (gitignore) |
| `.terraform.lock.hcl` | Provider checksum lock (commit this) |
| `terraform.tfstate` | Local state (gitignore — use remote in Day 3) |

---

## 7. Plan output — learn to read it

```
Terraform will perform the following actions:

  # aws_s3_bucket.lab will be created
  + resource "aws_s3_bucket" "lab" {
      + bucket = "devops-handbook-day1-123456789012"
      + id     = (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

| Symbol | Meaning |
|--------|---------|
| `+` | Create |
| `~` | Update in-place |
| `-` | Destroy |
| `-/+` | Force replace (destroy then create) |

---

## 8. Common mistakes (Day 1)

| Mistake | Fix |
|---------|-----|
| Committing `terraform.tfstate` | Add to `.gitignore`; use remote backend (Day 3) |
| Non-unique S3 bucket name | Include account ID or random suffix |
| Wrong region | Set `provider "aws" { region = ... }` |
| Editing state by hand | Use `terraform state` subcommands only |
| `-auto-approve` locally without reading plan | Apply only after reviewing plan |

---

## 9. Lab — First S3 bucket

Starter code: [labs/day1-s3-bucket](./labs/day1-s3-bucket/)

```bash
cd labs/day1-s3-bucket
cp terraform.tfvars.example terraform.tfvars   # optional overrides

terraform init
terraform plan
terraform apply

# Verify
terraform output bucket_name
aws s3 ls s3://$(terraform output -raw bucket_name)

terraform destroy
```

**Tasks:**

1. Apply the starter config; confirm bucket exists in AWS console or CLI.
2. Add `aws_s3_bucket_public_access_block` — re-plan and apply.
3. Change a tag value; observe `~` update in plan.
4. Run `terraform destroy` and confirm bucket is gone.

**Success criteria:** Clean `init`/`plan`/`apply`/`destroy` cycle with no state file committed to git.

---

## 10. Key takeaways

- Terraform workflow is **init → plan → apply**; state records what you manage.
- HCL blocks declare resources; references create dependency order.
- Provider version constraints belong in `required_providers`.
- Always tear down lab resources the same day.

**Next:** [Day 2 — Variables, outputs & data sources](../day2/)
