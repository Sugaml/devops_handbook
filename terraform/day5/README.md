# Day 5 — `count`, `for_each`, Dynamic Blocks & Lifecycle

**Goal:** Scale resources safely with meta-arguments, generate nested blocks dynamically, control create/destroy behavior with `lifecycle`, and use preconditions for guardrails.

**Time:** 5–6 hours

---

## 1. When to use `count` vs `for_each`

| `count` | `for_each` |
|---------|------------|
| Index-based list | Map or set of strings |
| `resource.name[0]` | `resource.name["key"]` |
| Removing middle item reshuffles indices | Stable keys by map key |
| Good for "0 or 1" optional resources | Good for named instances |

**Default recommendation:** Prefer **`for_each`** when each instance has a meaningful identity (bucket per team, subnet per AZ).

```hcl
# count — optional secondary bucket
resource "aws_s3_bucket" "backup" {
  count  = var.enable_backup ? 1 : 0
  bucket = "${var.project}-backup-${var.account_id}"
}

# for_each — one bucket per team
resource "aws_s3_bucket" "team" {
  for_each = var.teams   # map(string) or set(string)

  bucket = "${var.project}-${each.key}-${var.account_id}"
  tags = {
    Team = each.key
  }
}
```

Inside blocks: `count.index` vs `each.key` / `each.value`.

---

## 2. Module meta-arguments

```hcl
module "team_buckets" {
  for_each = toset(var.team_names)
  source   = "./modules/s3-bucket"

  bucket_name = "${var.project}-${each.key}"
  tags        = { Team = each.key }
}
```

Reference: `module.team_buckets["platform"].bucket_arn`

---

## 3. Dynamic blocks

Generate repeated nested blocks from a variable:

```hcl
variable "ingress_rules" {
  type = list(object({
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
  }))
  default = []
}

resource "aws_security_group" "app" {
  name   = "${var.project}-app"
  vpc_id = var.vpc_id

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
    }
  }
}
```

`dynamic` works for any repeated block type (`ingress`, `rule`, `filter`, etc.).

---

## 4. `lifecycle` block

```hcl
resource "aws_instance" "app" {
  ami           = var.ami_id
  instance_type = var.instance_type

  lifecycle {
  create_before_destroy = true
  prevent_destroy       = false   # set true for prod state buckets
  ignore_changes        = [tags["LastRebooted"]]
  }
}
```

| Argument | Use case |
|----------|----------|
| `create_before_destroy` | Zero-downtime replace (new resource before old deleted) |
| `prevent_destroy` | Safety rail on critical resources |
| `ignore_changes` | External systems mutate attribute (auto-scaling, k8s tags) |

**Replace triggers** (Terraform 1.2+):

```hcl
resource "terraform_data" "redeploy" {
  triggers_replace = {
    config_hash = sha256(file("${path.module}/config.json"))
  }
}
```

---

## 5. Preconditions and postconditions

```hcl
resource "aws_s3_bucket" "app" {
  bucket = var.bucket_name

  lifecycle {
    precondition {
      condition     = length(var.bucket_name) <= 63
      error_message = "S3 bucket name must be 63 characters or fewer."
    }
  }
}
```

Fails at **plan** time with a clear message — cheaper than failed apply.

---

## 6. `depends_on` with modules

```hcl
module "network" { ... }
module "app" {
  depends_on = [module.network]
}
```

Use sparingly — implicit references are preferred. Explicit `depends_on` when dependency is not visible in arguments (e.g. IAM propagation delay).

---

## 7. Lab — Multi-team buckets with `for_each`

Starter: [labs/day5-for-each](./labs/day5-for-each/)

```bash
cd labs/day5-for-each
terraform init
terraform plan -var-file=../../lab.tfvars
terraform apply -var-file=../../lab.tfvars

terraform state list
terraform output bucket_map

# Remove one team from tfvars, plan again — only that bucket destroyed
terraform destroy -var-file=../../lab.tfvars
```

**Tasks:**

1. Add dynamic `lifecycle_rule` block for buckets with `expire_days > 0`.
2. Convert one `count`-based optional resource to `for_each` and compare destroy behavior.
3. Add a precondition: team names must match `^[a-z]+$`.

**Success criteria:** Adding/removing a team key creates/destroys only that bucket; plan is predictable.

---

## 8. Key takeaways

- `for_each` preserves stable addresses; avoid `count` for long-lived named resources.
- Dynamic blocks keep security group / IAM policy rules DRY.
- `lifecycle` controls replace order and protects critical infra.
- Preconditions fail fast at plan time.

**Previous:** [Day 4 — Modules](../day4/) · **Next:** [Day 6 — Workspaces, testing & CI](../day6/)
