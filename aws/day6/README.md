# Day 6 — CLI Output, JMESPath, Filters & Pagination

**Goal:** Shape CLI output for humans and scripts; filter AWS resources efficiently; handle paginated APIs.

**Time:** 3–5 hours

**Services:** All (cross-cutting)

---

## 1. Output formats

```bash
aws ec2 describe-instances --output json    # default
aws ec2 describe-instances --output table
aws ec2 describe-instances --output text
aws ec2 describe-instances --output yaml

# Combine with query
aws ec2 describe-instances \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,InstanceType]' \
  --output table
```

---

## 2. JMESPath essentials

```bash
# Project fields
aws s3api list-buckets --query 'Buckets[].Name'

# Filter
aws ec2 describe-instances \
  --filters Name=instance-state-name,Values=running \
  --query 'Reservations[].Instances[?InstanceType==`t3.micro`].InstanceId'

# Flatten nested
aws iam list-users --query 'Users[*].[UserName,CreateDate]' --output table

# Length
aws ec2 describe-security-groups --query 'length(SecurityGroups)'

# Sort
aws ec2 describe-images --owners self \
  --query 'sort_by(Images,&CreationDate)[*].[ImageId,Name]'
```

Practice: [JMESPath tutorial](https://jmespath.org/tutorial.html)

---

## 3. Filters vs `--query`

| Mechanism | Where applied | Cost |
|-----------|---------------|------|
| `--filters` | Server-side (API) | Less data transferred |
| `--query` | Client-side (JMESPath) | After full page received |

```bash
aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=devops-handbook" \
           "Name=instance-state-name,Values=running"
```

---

## 4. Pagination

```bash
# Auto-paginated (default) — all pages
aws ec2 describe-instances --output text > /tmp/all-instances.txt

# Limit pages
aws s3api list-objects-v2 --bucket "$BUCKET" --max-items 100

# Manual token
aws ec2 describe-instances --max-items 5
aws ec2 describe-instances --starting-token "eyJ..."  # from NextToken

# Disable pager for scripts
export AWS_PAGER=""
```

---

## 5. Waiters and dry-run

```bash
aws ec2 wait instance-running --instance-ids i-xxx
aws ec2 wait instance-terminated --instance-ids i-xxx
aws rds wait db-instance-available --db-instance-identifier handbook-db

aws ec2 terminate-instances --instance-ids i-xxx --dry-run 2>&1 | grep -i dryrun
```

---

## 6. Script pattern

```bash
#!/usr/bin/env bash
set -euo pipefail
export AWS_PAGER=""

for id in $(aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=devops-handbook" \
  --query 'Reservations[].Instances[].InstanceId' --output text); do
  echo "Instance: $id"
  aws ec2 describe-instance-status --instance-ids "$id" \
    --query 'InstanceStatuses[0].SystemStatus.Status' --output text
done
```

---

## 7. Lab — Day 6

1. List all running instances in table format with Name tag, type, AZ.
2. Write a one-liner counting buckets per region (hint: `get-bucket-location`).
3. Export all security group IDs with open port 22 to a file.
4. Use `--generate-cli-skeleton` for `create-launch-template`; fill minimal fields.
5. Time `describe-instances` with and without `--filters` on a busy account.

**Previous:** [Day 5](../day5/) · **Next:** [Day 7 — Profiles & automation](../day7/)
