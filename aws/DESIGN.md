# AWS Handbook — Design & curriculum notes

## Goals

- **CLI-first**: Every day is actionable from a terminal; console steps are mentioned only when CLI is awkward.
- **DevOps trajectory**: Days 1–7 (identity + CLI craft) → 8–14 (network/compute/observability) → 15–21 (data/serverless/containers) → 22–30 (secrets, IaC, CI/CD, EKS, cost, org).
- **Service coverage**: IAM, EC2, VPC, S3, ELB, ASG, EBS, Route 53, CloudWatch, SNS/SQS, RDS, DynamoDB, Lambda, API Gateway, ECS/ECR, Secrets Manager, SSM, KMS, CloudFormation, CodeBuild/CodePipeline, EKS, WAF, Billing, Organizations/SSO.

## Pedagogy

| Pattern | Usage |
|---------|--------|
| Goal + time box | Sets expectations (3–6 h/day) |
| Tables | Service limits, comparison (ALB vs NLB) |
| Code blocks | Runnable `aws` commands |
| DevOps callout | CI runners, least privilege, tagging |
| Lab | Creates + verifies + **teardown** |
| Prev/Next links | Linear path with optional skips |

## Edge cases documented in days

- **Regional vs global**: S3 bucket names global; IAM global; most compute regional.
- **Eventually consistent**: IAM policy changes, S3 list-after-create — use retries in scripts (Day 7).
- **Pagination**: Default 1000 max; `--page-size`, `--max-items`, `aws s3` sync (Day 6).
- **Idempotency**: CloudFormation stacks, `create-stack` vs `update-stack` (Day 24).
- **IMDSv2**: EC2 metadata requires token (Day 4).

## Performance / cost optimizations

- Use **S3 Intelligent-Tiering** or lifecycle only when taught (Day 5); default Standard for labs.
- **GP3** over GP2 for new EBS (Day 12).
- **Graviton** (`t4g`, `m7g`) mentioned where AMI/arch matters (Day 3).
- **Interface VPC endpoints** vs NAT for AWS API traffic (Day 9).

## User feedback / iteration

- Extend Day 26 with GitHub Actions OIDC when users request GitHub-first CI.
- Optional add-on track: **Terraform** companion — [terraform/](../terraform/README.md) Week 1 (Days 1–7).

## Versioning

- Written for AWS CLI v2.x and APIs as of 2025–2026; verify deprecated flags with `aws help`.
