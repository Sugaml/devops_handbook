# Day 7 — Production Layout, IAM & Capstone Lab

**Goal:** Structure a professional Terraform repository for multiple environments, apply IAM least privilege for automation, wire remote state and modules together, and deploy a small but realistic stack (network + compute + storage).

**Time:** 6–8 hours

---

## 1. Production repository layout

```
infra/
├── modules/
│   ├── vpc/
│   ├── s3-bucket/
│   └── ec2-app/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── backend.tf
│   │   ├── dev.tfvars
│   │   └── versions.tf
│   └── prod/
│       └── ...
├── global/
│   └── iam/                 # CI roles, optional separate state
├── .github/workflows/
│   └── terraform.yml
├── .gitignore
└── README.md
```

| Principle | Rationale |
|-----------|-----------|
| **One state per blast radius** | VPC state separate from app state when teams scale |
| **Modules are generic** | No hard-coded `dev` inside `modules/vpc` |
| **Env dir = root module** | Run `terraform apply` from `environments/dev` |
| **Pin versions** | `versions.tf` locks Terraform + providers |
| **No secrets in git** | Secrets Manager, SSM, CI OIDC |

---

## 2. Splitting state (when to)

| Single state | Multiple states |
|--------------|-----------------|
| Small team, one app | Platform team owns VPC; app team owns services |
| Fast iteration | Reduce plan time and blast radius |
| Lab / capstone | Prod network rarely changes |

**Remote state data source** — read outputs from another stack:

```hcl
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = var.state_bucket
    key    = "dev/network/terraform.tfstate"
    region = var.region
  }
}

# Use: data.terraform_remote_state.network.outputs.vpc_id
```

---

## 3. IAM for Terraform automation

Humans and CI should use **roles**, not long-lived keys.

### Minimum CI role policy (illustrative — tighten per resource)

Attach to `github-terraform` or `terraform-deploy` role:

- `s3:GetObject`, `s3:PutObject` on state bucket prefix
- `dynamodb:GetItem`, `PutItem`, `DeleteItem` on lock table
- Service-specific create/read/update/delete for resources in scope

**DevOps note:** Use **OIDC** trust from GitHub/GitLab to AWS — see [AWS handbook Day 30](../../aws/README.md) patterns.

```hcl
# Human admin — separate break-glass role
# CI role — plan-only on PR, apply role assumable only from main branch workflow
```

Never run Terraform as account root.

---

## 4. Environment promotion flow

```
  dev.tfvars  ──PR──►  plan  ──merge──►  apply dev
                              │
                              └── promote tfvars / module version ──► staging ──► prod
```

| Stage | Gate |
|-------|------|
| Dev | Auto-apply or low-friction |
| Staging | Required review + plan artifact |
| Prod | Manual approval + change window |

Use **same modules**, different tfvars and backends.

---

## 5. Operational runbook snippets

### Before apply

```bash
terraform init -upgrade=false
terraform plan -out=tfplan -var-file=dev.tfvars
# Review: creates, destroys, replaces
```

### After failed apply

```bash
terraform state list
terraform refresh
terraform plan
# Partial state — fix config, re-apply; avoid manual console fixes
```

### Version upgrade

```bash
# Bump required_providers version in versions.tf
terraform init -upgrade
terraform plan   # expect provider-driven changes
```

---

## 6. Capstone architecture

```
                    Internet
                        │
                   [ Internet Gateway ]
                        │
              ┌─────────┴─────────┐
              │   Public subnet   │
              │   EC2 (t3.micro)  │── IAM instance profile (S3 read)
              └─────────┬─────────┘
                        │
              ┌─────────┴─────────┐
              │  Private subnet   │  (optional NAT — cost warning)
              └───────────────────┘

        S3 bucket (app assets) — encryption, public access blocked
```

Components in [labs/day7-capstone](./labs/day7-capstone/):

- `modules/vpc` — VPC, public subnet, IGW, route table
- `modules/s3-bucket` — reused from Day 4 pattern
- `modules/ec2-app` — instance, SG, IAM role/profile
- `environments/lab/` — wires modules, backend optional

---

## 7. Lab — Capstone deploy

```bash
cd labs/day7-capstone/environments/lab

# Optional: configure backend.tf from Day 3 bootstrap
terraform init
terraform plan -var-file=lab.tfvars
terraform apply -var-file=lab.tfvars

# Verify
terraform output
curl -s --max-time 5 "http://$(terraform output -raw public_ip):8080" || true
aws s3 ls s3://$(terraform output -raw assets_bucket)

terraform destroy -var-file=lab.tfvars
```

**Tasks:**

1. Add `prevent_destroy = true` on state bucket module in prod example (comment only in lab).
2. Split one output through `terraform_remote_state` mock — document how you'd split VPC/app state.
3. Write a 5-line runbook: "Rollback failed deploy" for your team wiki.
4. List three tags every resource should carry (Project, Environment, ManagedBy).

**Success criteria:** Full stack up, HTTP check responds (user-data installs a tiny web server), clean destroy with no leftover EC2 or EIP charges.

---

## 8. Professional checklist

Before calling Terraform "production ready" in your org:

- [ ] Remote state + locking on all roots
- [ ] `.gitignore` excludes state, `.terraform/`, `*.tfvars` with secrets
- [ ] `.terraform.lock.hcl` committed
- [ ] CI: fmt, validate, test, plan on PR
- [ ] Apply via pipeline with OIDC / short-lived creds
- [ ] Module and provider versions pinned
- [ ] Drift detection (scheduled plan)
- [ ] Documented ownership and runbooks
- [ ] Cost tags on all billable resources

---

## 9. Week 1 recap

| Day | You learned |
|-----|-------------|
| 1 | Workflow, HCL, first resource |
| 2 | Variables, outputs, data sources |
| 3 | State, remote backend, import, drift |
| 4 | Modules and composition |
| 5 | `count`, `for_each`, lifecycle |
| 6 | Workspaces vs dirs, test, CI |
| 7 | Production layout, IAM, capstone |

**What's next:** VPC deep dive, EKS, RDS, policy-as-code (Sentinel / OPA / `check`), and multi-account with AWS Organizations — extend this handbook or pair with [AWS](../../aws/README.md) and [Kubernetes](../../kubernetes/README.md) tracks.

---

## 10. Key takeaways

- Directory-per-environment beats workspace-only for prod isolation.
- IAM roles + OIDC are the standard for Terraform CI.
- Small modules composed in environment roots scale with teams.
- Capstone proves you can plan, apply, verify, and destroy safely.

**Previous:** [Day 6 — Workspaces, testing & CI](../day6/) · **Back to overview:** [Terraform handbook](../)
