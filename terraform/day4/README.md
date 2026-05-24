# Day 4 — Modules: Reusable Infrastructure Components

**Goal:** Extract repeated patterns into modules, pass inputs and outputs cleanly, version modules, and consume modules from local paths and the Terraform Registry.

**Time:** 5–6 hours

---

## 1. Why modules?

| Copy-paste `.tf` | Module |
|------------------|--------|
| Fix bug in 5 places | Fix once in module |
| Inconsistent tags | Enforced interface |
| Hard to test | Test module in isolation |

A **module** is a container of Terraform resources with an explicit **input/output contract**.

```
  root module (your project)
       │
       ├── module "storage"  ──► modules/s3-bucket/
       └── module "network"  ──► terraform-aws-modules/vpc/aws
```

---

## 2. Module structure

```
modules/s3-bucket/
├── main.tf
├── variables.tf
├── outputs.tf
└── README.md
```

**Root module** = directory where you run `terraform apply` (not necessarily named `root`).

**Child module** = called via `module` block.

---

## 3. Calling a local module

```hcl
module "app_bucket" {
  source = "./modules/s3-bucket"

  bucket_name         = local.bucket_name
  enable_versioning   = true
  enable_encryption   = true
  tags                = local.common_tags
}

output to module output:
# module.app_bucket.bucket_arn
```

Module block arguments map to module `variable` blocks. Only **exported** outputs are visible outside.

---

## 4. Module sources

| Source | Example |
|--------|---------|
| Local path | `source = "./modules/vpc"` |
| Git | `source = "git::https://github.com/org/repo.git//modules/vpc?ref=v1.2.0"` |
| Registry | `source = "terraform-aws-modules/s3-bucket/aws"` |
| S3 / GCS | `source = "s3::https://..."` |

**Production rule:** Pin module version:

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.8.1"
  # ...
}
```

---

## 5. Composition pattern

Build higher-level stacks from small modules:

```hcl
module "logs_bucket" {
  source      = "./modules/s3-bucket"
  bucket_name = "${var.project}-logs"
  tags        = local.common_tags
}

module "assets_bucket" {
  source      = "./modules/s3-bucket"
  bucket_name = "${var.project}-assets"
  tags        = local.common_tags
}
```

Each module instance has **separate state addresses**:

- `module.logs_bucket.aws_s3_bucket.this`
- `module.assets_bucket.aws_s3_bucket.this`

---

## 6. Passing providers to modules

When using provider aliases (multi-region / cross-account):

```hcl
module "replica" {
  source = "./modules/s3-bucket"
  providers = {
    aws = aws.replica_region
  }
}
```

Child module must declare:

```hcl
terraform {
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      configuration_aliases = [aws]
    }
  }
}
```

---

## 7. Module anti-patterns

| Anti-pattern | Better approach |
|--------------|-----------------|
| Mega-module (entire VPC + app + DB) | Small composable modules |
| Hidden provider config inside module | Pass providers explicitly when needed |
| Unpinned git `ref=main` | Pin tag or commit SHA |
| Module outputs everything | Export minimal stable contract |

---

## 8. Lab — Reusable S3 module

Structure:

```
labs/day4-modules/
├── main.tf              # calls module twice
├── variables.tf
├── outputs.tf
└── modules/
    └── s3-bucket/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

```bash
cd labs/day4-modules
terraform init
terraform plan -var-file=../../lab.tfvars
terraform apply -var-file=../../lab.tfvars

terraform state list | grep module
terraform output

terraform destroy -var-file=../../lab.tfvars
```

**Tasks:**

1. Add optional lifecycle rule variable to the module (expire objects after N days).
2. Create a third module instance via `for_each` over a map (preview Day 5).
3. Document module inputs/outputs in `modules/s3-bucket/README.md`.

**Success criteria:** Two buckets from one module; changing module code updates both on next plan.

---

## 9. Key takeaways

- Modules are functions for infrastructure — inputs, outputs, single responsibility.
- Pin versions for registry and git sources.
- Root module orchestrates; child modules encapsulate.
- State tracks `module.name.resource.type.name` addresses.

**Previous:** [Day 3 — State & backends](../day3/) · **Next:** [Day 5 — Meta-arguments & lifecycle](../day5/)
