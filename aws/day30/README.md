# Day 30 — Multi-Account, SSO & Production Runbooks

**Goal:** Operate like a platform team—Organizations, IAM Identity Center, cross-account roles, DR thinking, and incident CLI runbooks.

**Time:** 6–8 hours

**Services:** Organizations, IAM Identity Center, STS, Route 53, S3, CloudWatch

---

## 1. AWS Organizations (overview)

```bash
aws organizations describe-organization
aws organizations list-accounts
aws organizations list-organizational-units-for-parent --parent-id r-xxxx

# Service Control Policy (management account)
aws organizations list-policies --filter SERVICE_CONTROL_POLICY
```

Typical OU layout: **Security**, **Infrastructure**, **Workloads** (dev/stage/prod).

SCPs deny dangerous actions (e.g. `organizations:LeaveOrganization`, unapproved regions).

---

## 2. IAM Identity Center (SSO)

```bash
aws sso-admin list-instances
# Configure identity source (Identity Center directory or external IdP)

aws configure sso
# SSO start URL, SSO region, account/role selection → profile

aws sts get-caller-identity --profile handbook-prod-admin
```

**DevOps note:** Humans never use IAM users in prod; SSO roles with short sessions + MFA.

---

## 3. Cross-account deployment role

Trust in **workload account**:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "AWS": "arn:aws:iam::TOOLING_ACCOUNT:role/CIPipeline" },
    "Action": "sts:AssumeRole",
    "Condition": { "StringEquals": { "sts:ExternalId": "handbook-pipeline" } }
  }]
}
```

```bash
aws sts assume-role \
  --role-arn arn:aws:iam::WORKLOAD_ACCOUNT:role/DeployRole \
  --role-session-name release-1.2.3 \
  --external-id handbook-pipeline
```

---

## 4. Disaster recovery patterns

| Tier | RPO/RTO sketch | CLI tools |
|------|----------------|-----------|
| Backup/restore | Hours | RDS snapshots, EBS snapshots, S3 replication |
| Pilot light | Minutes–hours | ASG min=0, AMIs, Route 53 failover |
| Warm standby | Minutes | Smaller live stack in DR region |
| Multi-region active | Low | Global Accelerator, DynamoDB global tables |

```bash
# S3 cross-region replication
aws s3api put-bucket-replication --bucket "$BUCKET" --replication-configuration file://replication.json

# Route 53 health-checked failover (Day 13)
```

---

## 5. Incident runbook (CLI)

```bash
#!/usr/bin/env bash
# handbook-incident.sh — starter
set -euo pipefail
export AWS_PAGER=""
echo "=== Identity ==="
aws sts get-caller-identity
echo "=== Recent alarms ==="
aws cloudwatch describe-alarms --state-value ALARM \
  --query 'MetricAlarms[].AlarmName' --output table
echo "=== ASG activities ==="
aws autoscaling describe-scaling-activities --max-items 5
echo "=== Unhealthy targets ==="
aws elbv2 describe-target-health --target-group-arn "$TG_ARN" \
  --query 'TargetHealthDescriptions[?TargetHealth.State!=`healthy`]'
echo "=== Recent errors (logs) ==="
aws logs filter-log-events --log-group-name /handbook/app \
  --filter-pattern "ERROR" --limit 20
```

---

## 6. Production checklist

- [ ] No root access keys; SSO enforced
- [ ] CloudTrail enabled all regions → S3 + KMS
- [ ] GuardDuty, Security Hub enabled (security account)
- [ ] Default VPC removed or unused; custom VPC only
- [ ] IMDSv2 required; SSM Session Manager instead of SSH
- [ ] Secrets in Secrets Manager; no plaintext in Lambda env
- [ ] IaC (CloudFormation/Terraform) for all infrastructure
- [ ] Tags: `Project`, `Owner`, `Environment`, `CostCenter`
- [ ] Budgets + anomaly detection
- [ ] Runbooks and on-call dashboards tested quarterly

---

## 7. Capstone lab — Day 30

1. Configure SSO profile (or document steps for your org).
2. Assume cross-account role into a second sandbox account (if available).
3. Execute incident script against a failing ALB target (stop one instance).
4. Write one-page DR plan for handbook app (RDS + S3 + Route 53).
5. **Full teardown:** run account-wide tag search for `Project=devops-handbook` and delete all resources.

---

## Congratulations

You have practiced **30 days** of AWS CLI across identity, network, compute, storage, data, serverless, containers, security, IaC, CI/CD, Kubernetes, cost, and operations.

**Keep learning:** AWS Certified DevOps Engineer – Professional, Well-Architected Framework reviews, and contribute modules back to this handbook.

**Previous:** [Day 29](../day29/) · **Handbook home](../README.md)
