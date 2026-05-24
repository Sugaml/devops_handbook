# Day 7 — Profiles, Role Chains & Shell Automation

**Goal:** Configure multi-profile workflows, assume roles, wrap the CLI in scripts, and handle IAM propagation delays.

**Time:** 4–5 hours

**Services:** IAM, STS

---

## 1. Multiple profiles in `~/.aws/config`

```ini
[profile devops-handbook]
region = us-east-1
output = json

[profile handbook-staging]
role_arn = arn:aws:iam::STAGING_ACCOUNT:role/DevOpsDeploy
source_profile = devops-handbook
region = us-east-1
```

```bash
aws sts get-caller-identity --profile handbook-staging
AWS_PROFILE=handbook-staging aws s3 ls
```

---

## 2. Assume role helper

```bash
assume_handbook_role() {
  local role_arn="$1"
  local session="handbook-$(date +%s)"
  eval "$(aws sts assume-role \
    --role-arn "$role_arn" \
    --role-session-name "$session" \
    --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' \
    --output text | awk '{print "export AWS_ACCESS_KEY_ID="$1"\nexport AWS_SECRET_ACCESS_KEY="$2"\nexport AWS_SESSION_TOKEN="$3}')"
  aws sts get-caller-identity
}
```

Clear session:

```bash
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
export AWS_PROFILE=devops-handbook
```

---

## 3. Retry for IAM eventual consistency

```bash
retry() {
  local n=0 max=10 delay=3
  until "$@"; do
    n=$((n + 1))
    [[ $n -ge $max ]] && return 1
    sleep "$delay"
  done
}
retry aws iam attach-role-policy --role-name MyRole --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess
```

---

## 4. Useful aliases

```bash
alias awswho='aws sts get-caller-identity --output table'
alias awsreg='aws configure get region'
alias ec2ls='aws ec2 describe-instances --query "Reservations[].Instances[].[Tags[?Key==\`Name\`].Value|[0],InstanceId,State.Name]" --output table'
```

---

## 5. `aws shell` (interactive)

```bash
aws shell
# aws> ec2 describe-instances --output table
# aws> .quit
```

---

## 6. Lab — Day 7

1. Add second profile that assumes a role (same account lab role is fine).
2. Script: tag all instances missing `Project` tag with default value (read-only dry-run first).
3. Script: stop all instances tagged `Project=devops-handbook` in `stopped` schedule (document safety checks).
4. Measure IAM policy attach → `simulate-principal-policy` success delay with retry loop.

**Previous:** [Day 6](../day6/) · **Next:** [Day 8 — VPC fundamentals](../day8/)
