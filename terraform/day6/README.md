# Day 6 — Workspaces, Testing, Linting & CI/CD

**Goal:** Use workspaces appropriately, write `terraform test` cases, enforce quality with `fmt`/`validate`/tflint, and run plan in GitHub Actions (apply from protected branches only).

**Time:** 5–6 hours

---

## 1. Workspaces — what they are (and are not)

Workspaces split **state** within the **same backend key prefix**:

```bash
terraform workspace list
terraform workspace new dev
terraform workspace select staging
terraform workspace show
```

Same code + different workspace → different state file (`env:/dev/...` in S3).

| Good for | Poor for |
|----------|----------|
| Quick personal experiments | Long-lived prod vs dev isolation |
| Ephemeral preview envs | Different IAM / accounts |
| Same account, same region | Compliance boundaries |

**Production pattern:** Separate directories + separate state keys (or accounts), not workspaces alone:

```
environments/
  dev/
    main.tf
    backend.tf      # key = "dev/network/terraform.tfstate"
  prod/
    main.tf
    backend.tf      # key = "prod/network/terraform.tfstate"
```

---

## 2. Quality gate commands

```bash
terraform fmt -check -recursive   # CI: fail if not formatted
terraform validate
terraform plan -out=tfplan          # save plan artifact
terraform show -json tfplan > plan.json
```

### tflint

```bash
# Install: https://github.com/terraform-linters/tflint
tflint --init
tflint --recursive
```

Catches unused declarations, invalid instance types, deprecated resources.

---

## 3. `terraform test` (native tests)

**Requires Terraform 1.6+** (CI workflow uses 1.9.0). On 1.5.x, skip to section 4 and rely on `validate` + `plan`.

Terraform 1.6+ supports **`tests/`** directory:

```hcl
# tests/s3_bucket.tftest.hcl
run "valid_plan" {
  command = plan

  variables {
    project     = "test"
    environment = "lab"
  }

  assert {
    condition     = aws_s3_bucket.app.bucket != ""
    error_message = "Bucket must be planned"
  }
}
```

```bash
terraform test
```

Use **mock providers** for fast unit-style tests without AWS calls (see HashiCorp docs for `override_provider`).

---

## 4. CI/CD pipeline pattern

```
  PR opened
     │
     ├── terraform fmt -check
     ├── terraform init -backend=false   # validate only
     ├── terraform validate
     ├── tflint
     ├── terraform plan (comment on PR)
     └── terraform test

  merge to main
     │
     └── terraform apply (manual approval or auto with policy)
```

**DevOps rules:**

- **Plan on PR**, apply on merge (or release tag).
- Use **OIDC** to AWS — no long-lived `AWS_ACCESS_KEY_ID` in GitHub secrets.
- Store plan file; apply **that** plan: `terraform apply tfplan`.
- Set `TF_IN_AUTOMATION=1` in CI.

---

## 5. GitHub Actions example

See [labs/day6-ci/.github/workflows/terraform.yml](./labs/day6-ci/.github/workflows/terraform.yml).

Key steps:

```yaml
- uses: hashicorp/setup-terraform@v3
  with:
    terraform_version: 1.9.0

- run: terraform init -backend=false
- run: terraform fmt -check -recursive
- run: terraform validate
- run: terraform test
```

For plan with AWS:

```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789012:role/github-terraform
    aws-region: us-east-1

- run: terraform init
- run: terraform plan -no-color -out=tfplan
```

---

## 6. Plan artifacts and security

| Practice | Why |
|----------|-----|
| `-out=tfplan` | Apply exactly what was reviewed |
| `-compact-warnings` | Cleaner CI logs |
| Mask sensitive values | Provider may mark outputs sensitive |
| Separate plan/apply jobs | Apply role narrower than plan role (optional) |

Never post full plan with secrets to public PR comments — use private CI or sanitized summary.

---

## 7. Lab — Tests and CI skeleton

```bash
cd labs/day6-ci
terraform init
terraform test
terraform fmt -check -recursive
terraform validate

# Optional: act or push to GitHub to trigger workflow
```

**Tasks:**

1. Add a failing test; fix config until `terraform test` passes.
2. Add `tflint` rule or plugin for AWS; fix one lint finding.
3. Extend workflow with `-var-file` for a `ci.tfvars`.
4. Document in README when you would **not** use workspaces for prod.

**Success criteria:** `terraform test` green locally; workflow file validates on push.

---

## 8. Key takeaways

- Workspaces are lightweight state switchers — not a full multi-env strategy.
- `fmt`, `validate`, tflint, and `test` belong in every pipeline.
- Plan on PR, apply from trusted path with OIDC credentials.
- Saved plan files tie review to execution.

**Previous:** [Day 5 — Meta-arguments](../day5/) · **Next:** [Day 7 — Production layout & capstone](../day7/)
