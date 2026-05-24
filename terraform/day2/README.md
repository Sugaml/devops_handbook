# Day 2 — Variables, Outputs, Locals & Data Sources

**Goal:** Parameterize infrastructure with typed variables and validation, expose values with outputs, reduce duplication with `locals`, and query existing infrastructure with data sources.

**Time:** 4–5 hours

---

## 1. Why parameterize?

| Hard-coded values | Variables + tfvars |
|-------------------|---------------------|
| One config per environment | Same module, different `dev.tfvars` / `prod.tfvars` |
| Secrets in `.tf` files | `TF_VAR_*` env vars or CI secrets |
| Copy-paste drift | Single source of truth |

**DevOps note:** CI/CD pipelines pass `-var-file=prod.tfvars` or environment-specific `TF_VAR_*` values — never edit `.tf` files per environment.

---

## 2. Variable types

```hcl
variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "allowed_cidrs" {
  description = "CIDR blocks allowed to reach the bucket policy"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Additional resource tags"
  type        = map(string)
  default     = {}
}

variable "retention" {
  description = "Object retention settings"
  type = object({
    enabled = bool
    days    = number
  })
  default = {
    enabled = false
    days    = 30
  }
}
```

| Type | Example value |
|------|---------------|
| `string` | `"us-east-1"` |
| `number` | `30` |
| `bool` | `true` |
| `list(T)` | `["a", "b"]` |
| `set(T)` | unique list |
| `map(T)` | `{ key = "value" }` |
| `object({...})` | structured config |

---

## 3. Validation and preconditions

```hcl
variable "environment" {
  type = string

  validation {
    condition     = contains(["lab", "dev", "staging", "prod"], var.environment)
    error_message = "environment must be lab, dev, staging, or prod."
  }
}
```

Terraform 1.5+ also supports **`check` blocks** and **`lifecycle.precondition`** on resources (Day 5).

Set variables from:

```bash
# CLI
terraform apply -var="environment=dev"

# File (preferred)
terraform apply -var-file="dev.tfvars"

# Environment (CI)
export TF_VAR_environment=dev
```

---

## 4. Locals — computed values

```hcl
locals {
  common_tags = merge(
    {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags,
  )

  bucket_name = "${var.project}-${var.environment}-${data.aws_caller_identity.current.account_id}"
}
```

Use `local.common_tags` anywhere you need consistent naming without repeating `merge()` logic.

---

## 5. Outputs

```hcl
output "bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.app.id
}

output "bucket_domain" {
  description = "Regional domain name"
  value       = aws_s3_bucket.app.bucket_regional_domain_name
}

output "db_password" {
  value     = random_password.db.result
  sensitive = true
}
```

```bash
terraform output
terraform output -raw bucket_name
terraform output -json | jq .
```

**Never** echo sensitive outputs in CI logs. Mark secrets `sensitive = true`.

---

## 6. Data sources in depth

Data sources are **read-only** — Terraform never creates or destroys them.

```hcl
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "aws_vpc" "default" {
  default = true
}
```

Reference: `data.aws_ami.amazon_linux.id`, `data.aws_availability_zones.available.names`

| Resource vs data | Use when |
|------------------|----------|
| `resource` | You own lifecycle (create/update/delete) |
| `data` | Lookup existing infra (AMI, VPC, Route53 zone) |

---

## 7. Provider configuration patterns

```hcl
provider "aws" {
  region = var.region

  default_tags {
    tags = local.common_tags
  }
}

# Assume role (cross-account — production pattern)
provider "aws" {
  alias  = "network"
  region = var.region

  assume_role {
    role_arn = var.network_account_role_arn
  }
}
```

`default_tags` (AWS provider 3.x+) applies tags to all supported resources automatically.

---

## 8. tfvars and git hygiene

```
environments/
  lab.tfvars
  dev.tfvars
  prod.tfvars   # no secrets — reference Secrets Manager in prod
terraform.tfvars.example   # committed template
.gitignore                   # ignores terraform.tfvars, *.auto.tfvars
```

Example `lab.tfvars`:

```hcl
region      = "us-east-1"
project     = "devops-handbook"
environment = "lab"

tags = {
  Owner = "you@example.com"
}
```

---

## 9. Lab — Parameterized storage stack

Starter: [labs/day2-parameterized](./labs/day2-parameterized/)

```bash
cd labs/day2-parameterized
terraform init
terraform plan -var-file=../../lab.tfvars
terraform apply -var-file=../../lab.tfvars

terraform output
aws s3api get-bucket-tagging --bucket $(terraform output -raw bucket_name)

terraform destroy -var-file=../../lab.tfvars
```

**Tasks:**

1. Add a validation rule: `project` must be 3–20 chars, lowercase alphanumeric + hyphens.
2. Add output `availability_zones` from `data.aws_availability_zones`.
3. Override `tags` via `-var='tags={CostCenter="learning"}'` and re-apply.
4. Introduce intentional validation failure; read the error message.

**Success criteria:** Same code deploys with different tfvars; outputs are usable by downstream stacks.

---

## 10. Key takeaways

- Variables make modules reusable; validation catches mistakes at plan time.
- Locals keep DRY tag/name logic out of every resource block.
- Data sources integrate with existing cloud resources without importing state.
- Sensitive values belong in CI secrets or AWS Secrets Manager — not in git.

**Previous:** [Day 1 — Install & first resources](../day1/) · **Next:** [Day 3 — State & remote backends](../day3/)
