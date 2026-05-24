# Terraform for DevOps — 7-Day Handbook

A practical, hands-on path from your first `terraform apply` to production-grade Infrastructure as Code. Each day combines **concepts**, **copy-paste examples**, and a **lab** you run in a personal sandbox account.

Week 1 takes you from basics to professional patterns. Days 8–30 (networking, Kubernetes, policy, multi-account) are planned as follow-on tracks.

## Structure — Week 1 (Foundations to Professional)

| Day | Topic | Focus | Folder |
|-----|--------|-------|--------|
| 1 | Install, workflow, first resources | init / plan / apply / destroy, HCL basics | [day1](./day1/) |
| 2 | Variables, outputs, data sources | Input validation, locals, provider config | [day2](./day2/) |
| 3 | State & remote backends | S3 + DynamoDB locking, import, drift | [day3](./day3/) |
| 4 | Modules | Reusable components, versioning, registry | [day4](./day4/) |
| 5 | Meta-arguments & lifecycle | `count`, `for_each`, dynamic blocks, `lifecycle` | [day5](./day5/) |
| 6 | Workspaces, testing & CI | `terraform test`, fmt/validate, GitHub Actions | [day6](./day6/) |
| 7 | Production layout & capstone | Multi-env structure, IAM, full stack lab | [day7](./day7/) |

## Prerequisites

- Comfortable Linux shell ([Linux handbook](../linux/README.md) Days 1–3 recommended).
- AWS account with CLI configured ([AWS handbook](../aws/README.md) Day 1–2 recommended).
- **Never** commit `.tfstate`, `.terraform/`, or secrets to git.

## How to use this handbook

1. Complete **Day 1** setup (Terraform install, AWS profile) before anything else.
2. Run every command yourself; use `terraform plan` before every `apply`.
3. Finish each day's **Lab** and run **teardown** (`terraform destroy`) to avoid surprise bills.
4. Keep a personal repo of labs — what you build in 7 days becomes your IaC portfolio.
5. Read the **DevOps callout** boxes; they explain what changes in CI/CD and at scale.

## Recommended lab setup

```bash
# macOS
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Linux (amd64) — check https://developer.hashicorp.com/terraform/install for your arch
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

terraform version   # Terraform v1.9+ recommended

# Helpers used throughout
brew install jq tflint   # macOS
sudo apt install -y jq   # Debian/Ubuntu; install tflint from GitHub releases

# AWS profile from AWS handbook
export AWS_PROFILE=devops-handbook
export AWS_REGION=us-east-1
export TF_VAR_region=$AWS_REGION
```

### Safe lab defaults

```bash
export TF_IN_AUTOMATION=1          # cleaner non-interactive output in CI
export TF_INPUT=0                  # disable interactive prompts in scripts
export TF_CLI_ARGS_plan="-compact-warnings"

# Tag everything you create
export TF_VAR_project=devops-handbook
export TF_VAR_environment=lab
```

## Cost & safety

| Resource | Cost note |
|----------|-----------|
| S3 bucket | Pennies for storage — **empty and delete after each lab** |
| DynamoDB (state lock) | On-demand, negligible for labs — delete table on Day 3 teardown |
| EC2 / ALB (Day 7 capstone) | Hourly — use `t3.micro`, destroy same session |

Always run `terraform destroy` at the end of each lab. Pin provider versions; never use `-target` in production pipelines without understanding blast radius.

## Design notes

- Examples target **Terraform 1.5+** (optional attributes, `import` blocks, `terraform test`).
- Primary provider is **hashicorp/aws**; patterns apply to Azure, GCP, and others.
- Sample code lives in each day's `labs/` folder; starter files are copy-paste ready.
- Curriculum map and decisions: [DESIGN.md](./DESIGN.md).

## Progress tracker

```
[ ] Day 1  [ ] Day 4  [ ] Day 7
[ ] Day 2  [ ] Day 5
[ ] Day 3  [ ] Day 6
```

## Related handbooks

- [AWS for DevOps](../aws/README.md) — credentials, S3, VPC, IAM
- [Linux for DevOps](../linux/README.md) — shell, SSH, scripting
- [Kubernetes for DevOps](../kubernetes/README.md) — EKS and in-cluster IaC (Helm, GitOps)
