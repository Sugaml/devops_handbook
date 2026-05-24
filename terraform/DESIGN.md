# Terraform Handbook — Design & curriculum notes

## Goals

- **Hands-on first**: Every day produces working Terraform you can `plan` and `apply`.
- **DevOps trajectory**: Day 1 (workflow) → 2 (parameterization) → 3 (state) → 4 (modules) → 5 (scale patterns) → 6 (CI/test) → 7 (production layout + capstone).
- **AWS-aligned**: Labs use `hashicorp/aws`; concepts transfer to other providers.

## Pedagogy

| Pattern | Usage |
|---------|--------|
| Goal + time box | Sets expectations (4–6 h/day) |
| Tables | HCL types, state commands, anti-patterns |
| Code blocks | Runnable Terraform and shell commands |
| DevOps callout | CI pipelines, remote state, least privilege |
| Lab | Creates + verifies + **teardown** |
| Prev/Next links | Linear path; Day 7 capstone reuses Days 1–6 |

## Edge cases documented in days

- **State is the source of truth** — manual console edits cause drift (Day 3).
- **Sensitive outputs** — never log secrets from `terraform output` in CI (Day 2).
- **Module `count` vs `for_each`** — address stability and destroy semantics (Day 5).
- **Backend bootstrap** — chicken-and-egg for S3/DynamoDB backend (Day 3).
- **Provider aliases** — multi-region and cross-account patterns (Day 7).

## Performance / cost optimizations

- **S3 lifecycle** on state bucket — versioning + noncurrent expiration (Day 3).
- **`for_each` over `count`** when resource identity is map-key driven (Day 5).
- **Separate state per environment** — not workspaces alone at scale (Day 7).
- **Plan-only in PR** — apply from protected branch only (Day 6).

## User feedback / iteration

- Extend Week 2 with VPC, EKS, and RDS when users complete Week 1.
- Optional add-on: **OpenTofu** compatibility notes (same HCL, different binary).
- Policy-as-code track (Sentinel, OPA, `check` blocks) planned for Day 15+.

## Versioning

- Written for Terraform **1.5+** and AWS provider **5.x** as of 2025–2026.
- Verify provider schema with `terraform providers schema -json` when upgrading.
