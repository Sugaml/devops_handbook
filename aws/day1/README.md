# Day 1 — AWS Account, Regions & CLI Setup

**Goal:** Understand the AWS global model, install AWS CLI v2, configure credentials safely, and verify identity with STS.

**Time:** 3–5 hours

**Services:** IAM (intro), STS, Account

---

## 1. AWS global model

| Concept | Scope | CLI implication |
|---------|--------|-----------------|
| Region | Isolated geographic area (`us-east-1`) | Most commands need `--region` or profile default |
| Availability Zone | Data center within region (`us-east-1a`) | EC2 subnets map to AZs |
| Edge location | CDN / Route 53 edge | CloudFront, global accelerator |
| Account ID | 12-digit identifier | Used in ARNs, bucket policies |

```bash
# List enabled regions for your account
aws account list-regions --region-opt-status-enabled ENABLED \
  --query 'Regions[].RegionName' --output table

# Describe one region
aws ec2 describe-regions --region-names us-east-1 us-west-2 \
  --query 'Regions[].{Name:RegionName,Endpoint:Endpoint}' --output table
```

**DevOps note:** CI pipelines should pin `AWS_REGION` explicitly—never rely on implicit defaults across runners.

---

## 2. Install AWS CLI v2

```bash
# macOS
curl -fsSL "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o /tmp/AWSCLIV2.pkg
sudo installer -pkg /tmp/AWSCLIV2.pkg -target /
aws --version   # aws-cli/2.x ...

# Linux x86_64
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
unzip -q /tmp/awscliv2.zip -d /tmp && sudo /tmp/aws/install --update

# Shell completion (bash)
complete -C '/usr/local/bin/aws_completer' aws
```

Upgrade in place: re-run the installer or `aws --version` after package update.

---

## 3. Configure credentials (the right way)

**Never** create access keys for the root user. Use:

1. **IAM Identity Center (SSO)** — best for humans (Day 30 deep dive).
2. **IAM user** with MFA — acceptable for dedicated lab admin.
3. **IAM role** — for EC2, Lambda, GitHub OIDC (production default).

### Named profile (interactive access key — lab only)

```bash
aws configure --profile devops-handbook
# AWS Access Key ID: AKIA...
# AWS Secret Access Key: ...
# Default region name: us-east-1
# Default output format: json

export AWS_PROFILE=devops-handbook
aws sts get-caller-identity
```

Files created:

| File | Purpose |
|------|---------|
| `~/.aws/credentials` | Access keys per profile |
| `~/.aws/config` | Region, output, role chains, SSO |

```bash
# View config (redact before sharing)
aws configure list
aws configure list-profiles
cat ~/.aws/config
```

### Environment variables (CI / temporary)

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...    # required for assumed-role temp creds
export AWS_REGION=us-east-1
```

---

## 4. Verify identity with STS

```bash
aws sts get-caller-identity
# Account, Arn, UserId

aws sts get-caller-identity --output table
aws sts get-caller-identity --query Account --output text
```

Decode who you are:

| Arn pattern | Meaning |
|-------------|---------|
| `arn:aws:iam::123456789012:user/alice` | IAM user |
| `arn:aws:sts::123456789012:assumed-role/RoleName/session` | Assumed role |
| `arn:aws:iam::123456789012:root` | Root — fix this immediately |

---

## 5. First service calls

```bash
# Account alias (optional, global)
aws iam list-account-aliases
aws iam create-account-alias --account-alias my-devops-lab 2>/dev/null || true

# Service quotas (example)
aws service-quotas list-service-quotas \
  --service-code ec2 \
  --query 'Quotas[?QuotaName==`Running On-Demand Standard instances`]' \
  --max-items 1

# Help system — learn any API
aws ec2 help
aws ec2 describe-instances help
aws ec2 describe-instances --generate-cli-skeleton > /tmp/describe-instances.json
```

---

## 6. CLI ergonomics

```bash
export AWS_PAGER=""                    # scripts: no interactive pager
export AWS_DEFAULT_OUTPUT=json
export AWS_PROFILE=devops-handbook

# Timestamped debug (support tickets)
aws sts get-caller-identity --debug 2>&1 | tail -20

# Dry run (where supported, e.g. EC2 terminate)
aws ec2 terminate-instances --instance-ids i-xxx --dry-run
```

---

## 7. Lab — Day 1

1. Create a dedicated IAM admin user `handbook-admin` in the console (or Day 2 CLI) with MFA.
2. Install CLI v2; configure profile `devops-handbook`.
3. Run `aws sts get-caller-identity` and record Account ID in your notes.
4. List all available regions; pick a home region (e.g. `us-east-1`).
5. Set shell exports in `~/.bashrc` or `~/.zshrc`: `AWS_PROFILE`, `AWS_REGION`, `AWS_PAGER=""`.
6. Run `aws ec2 describe-regions --output table` and confirm no auth errors.

**Success criteria:** CLI returns your account ID; you are **not** using root access keys.

---

## 8. Key takeaways

- Regions are explicit; automation must set them.
- Profiles separate dev/stage/prod credentials on one laptop.
- STS is the source of truth for "who am I right now?"

**Next:** [Day 2 — IAM users, roles & policies](../day2/)
