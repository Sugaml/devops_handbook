# AWS CLI for DevOps — 30-Day Handbook

A practical, CLI-first path from AWS account setup to production-grade multi-account operations. Each day combines **service concepts**, **copy-paste commands**, and a **hands-on lab** you run in a personal sandbox account.

## Structure

### Week 1 — Foundations & identity

| Day | Topic | Services | Folder |
|-----|--------|----------|--------|
| 1 | Account, regions, CLI install & configure | IAM (intro), STS | [day1](./day1/) |
| 2 | IAM users, groups, roles, policies | IAM | [day2](./day2/) |
| 3 | EC2 instances, AMIs, key pairs | EC2 | [day3](./day3/) |
| 4 | Security groups, elastic IPs, instance metadata | EC2 | [day4](./day4/) |
| 5 | S3 buckets, objects, versioning | S3 | [day5](./day5/) |
| 6 | CLI output, JMESPath, pagination, `--query` | All | [day6](./day6/) |
| 7 | Profiles, assume-role, shell automation | IAM, STS | [day7](./day7/) |

### Week 2 — Networking & compute at scale

| Day | Topic | Services | Folder |
|-----|--------|----------|--------|
| 8 | VPC, subnets, route tables, IGW | VPC, EC2 | [day8](./day8/) |
| 9 | NAT Gateway, NACLs, VPC endpoints | VPC | [day9](./day9/) |
| 10 | Application & Network Load Balancers | ELB (v2) | [day10](./day10/) |
| 11 | Auto Scaling groups & launch templates | Auto Scaling, EC2 | [day11](./day11/) |
| 12 | EBS volumes, snapshots, AMIs | EBS, EC2 | [day12](./day12/) |
| 13 | Route 53 hosted zones & records | Route 53 | [day13](./day13/) |
| 14 | CloudWatch metrics, alarms, dashboards | CloudWatch | [day14](./day14/) |

### Week 3 — Observability, data & serverless

| Day | Topic | Services | Folder |
|-----|--------|----------|--------|
| 15 | CloudWatch Logs & log insights | CloudWatch Logs | [day15](./day15/) |
| 16 | SNS topics & SQS queues | SNS, SQS | [day16](./day16/) |
| 17 | RDS instances, snapshots, parameter groups | RDS | [day17](./day17/) |
| 18 | DynamoDB tables & indexes | DynamoDB | [day18](./day18/) |
| 19 | Lambda functions, versions, aliases | Lambda | [day19](./day19/) |
| 20 | API Gateway REST APIs | API Gateway | [day20](./day20/) |
| 21 | ECS clusters, tasks, services | ECS, ECR | [day21](./day21/) |

### Week 4 — Security, automation & production

| Day | Topic | Services | Folder |
|-----|--------|----------|--------|
| 22 | Secrets Manager & SSM Parameter Store | Secrets Manager, SSM | [day22](./day22/) |
| 23 | KMS keys, encryption at rest | KMS | [day23](./day23/) |
| 24 | CloudFormation stacks via CLI | CloudFormation | [day24](./day24/) |
| 25 | Systems Manager: Session Manager, Run Command | SSM | [day25](./day25/) |
| 26 | CodeBuild & CodePipeline | CodeBuild, CodePipeline | [day26](./day26/) |
| 27 | EKS clusters & `kubectl` integration | EKS | [day27](./day27/) |
| 28 | WAF, Shield (basics), security groups review | WAF, EC2 | [day28](./day28/) |
| 29 | Tagging strategy, Cost Explorer, budgets | Billing, CE | [day29](./day29/) |
| 30 | Multi-account, SSO, DR patterns, runbooks | Organizations, IAM Identity Center | [day30](./day30/) |

## Prerequisites

- Comfort with Linux shell ([Linux handbook](../linux/README.md) Day 1–3 recommended).
- A **personal AWS account** (Free Tier eligible) or AWS Educate / sandbox OU.
- **Never** use root access keys; use IAM Identity Center or an IAM admin user for labs.

## How to use this handbook

1. Complete **Day 1** setup (CLI v2, region, named profile) before anything else.
2. Run every command in your own account; use `--dry-run` where supported before destructive actions.
3. Finish each day's **Lab** and tear down billable resources (NAT, RDS, NAT GW, etc.).
4. Keep a personal cheat sheet of `aws` commands and JMESPath queries you reuse.
5. Optional: track spend daily in **Billing → Cost Explorer** (Day 29 goes deeper).

## Recommended lab setup

```bash
# Install AWS CLI v2 (macOS)
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o /tmp/AWSCLIV2.pkg
sudo installer -pkg /tmp/AWSCLIV2.pkg -target /

# Linux (x86_64)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
unzip -q /tmp/awscliv2.zip -d /tmp && sudo /tmp/aws/install

# Verify
aws --version
aws sts get-caller-identity

# Helpers used throughout
brew install jq   # macOS
sudo apt install -y jq  # Debian/Ubuntu

# Session name for audit trails
export AWS_PAGER=""          # disable less pager for scripts
export AWS_DEFAULT_OUTPUT=json
```

### Safe lab defaults

```bash
export AWS_PROFILE=devops-handbook
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=$AWS_REGION

# Tag everything you create
export LAB_TAG_KEY=Project
export LAB_TAG_VALUE=devops-handbook
```

## Cost & safety

| Resource | Cost note |
|----------|-----------|
| NAT Gateway | ~$0.045/hr + data — **delete after Day 9 lab** |
| ALB | ~$0.0225/hr — terminate after Day 10–11 labs |
| RDS / ElastiCache | Hourly — use `db.t3.micro`, delete same day |
| EKS | Control plane ~$0.10/hr — Day 27 is short-lived cluster only |

Always run teardown commands in each day's lab. Use **AWS Budgets** alerts (Day 29).

## Design notes

- Commands target **AWS CLI v2** syntax (`aws <service> <operation>`).
- Examples use `us-east-1`; replace region where your service requires it (e.g. CloudFront, some ACM certs).
- Production callouts highlight what changes in CI/CD, Terraform, and multi-account setups.
- Curriculum map and decisions: [DESIGN.md](./DESIGN.md).

## Related handbooks

- [Linux for DevOps](../linux/README.md) — shell, SSH, systemd
- [Docker for DevOps](../docker/README.md) — containers before ECS/EKS days
