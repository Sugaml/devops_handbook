# Day 2 — IAM: Users, Groups, Roles & Policies

**Goal:** Model identity and authorization with IAM; create users, groups, roles, and JSON policies entirely from the CLI.

**Time:** 4–6 hours

**Services:** IAM

---

## 1. IAM building blocks

| Entity | Purpose | Long-lived creds? |
|--------|---------|-------------------|
| User | Human or long-lived service | Yes (access keys — avoid) |
| Group | Permission bundle for users | No |
| Role | Assumed by AWS services or federated users | Temporary via STS |
| Policy | JSON document of Allow/Deny | Attached to above |

**ARN format:** `arn:aws:iam::ACCOUNT:policy/NAME`

---

## 2. Users and access keys

```bash
# Create user (no console login yet)
aws iam create-user --user-name handbook-deploy

# Attach AWS managed policy (lab only — too broad for prod)
aws iam attach-user-policy \
  --user-name handbook-deploy \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

# List users
aws iam list-users --query 'Users[].UserName' --output table

# Access keys (prefer roles in production)
aws iam create-access-key --user-name handbook-deploy
# SAVE SecretAccessKey once — it is not retrievable again

aws iam list-access-keys --user-name handbook-deploy
aws iam update-access-key --user-name handbook-deploy \
  --access-key-id AKIA... --status Inactive
aws iam delete-access-key --user-name handbook-deploy --access-key-id AKIA...
```

---

## 3. Groups

```bash
aws iam create-group --group-name devops-readonly
aws iam attach-group-policy \
  --group-name devops-readonly \
  --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess

aws iam add-user-to-group --group-name devops-readonly --user-name handbook-deploy
aws iam get-group --group-name devops-readonly
```

---

## 4. Custom policy (least privilege)

Create `s3-lab-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListBuckets",
      "Effect": "Allow",
      "Action": ["s3:ListAllMyBuckets", "s3:GetBucketLocation"],
      "Resource": "*"
    },
    {
      "Sid": "ObjectAccessInLabBucket",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::devops-handbook-*/*"
    }
  ]
}
```

```bash
aws iam create-policy \
  --policy-name DevOpsHandbookS3Lab \
  --policy-document file://s3-lab-policy.json

# Get policy ARN from output, then attach to user or group
aws iam attach-user-policy \
  --user-name handbook-deploy \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/DevOpsHandbookS3Lab
```

Validate policy:

```bash
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::ACCOUNT_ID:user/handbook-deploy \
  --action-names s3:ListAllMyBuckets s3:DeleteBucket \
  --output table
```

---

## 5. Roles and trust policies

EC2 instance role trust policy `ec2-trust.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "ec2.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

```bash
aws iam create-role \
  --role-name EC2-S3-ReadRole \
  --assume-role-policy-document file://ec2-trust.json

aws iam attach-role-policy \
  --role-name EC2-S3-ReadRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

# Instance profile (required to attach role to EC2)
aws iam create-instance-profile --instance-profile-name EC2-S3-ReadProfile
aws iam add-role-to-instance-profile \
  --instance-profile-name EC2-S3-ReadProfile \
  --role-name EC2-S3-ReadRole
```

Assume role from CLI (cross-account or elevated session):

```bash
aws sts assume-role \
  --role-arn arn:aws:iam::ACCOUNT_ID:role/EC2-S3-ReadRole \
  --role-session-name cli-lab \
  --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' \
  --output text
```

---

## 6. MFA and password policy

```bash
aws iam get-account-password-policy 2>/dev/null || \
  aws iam update-account-password-policy \
    --minimum-password-length 14 \
    --require-symbols --require-numbers \
    --require-uppercase-characters --require-lowercase-characters \
    --max-password-age 90

# Enable MFA device for your admin user (virtual — console QR, then)
aws iam enable-mfa-device --user-name handbook-admin \
  --serial-number arn:aws:iam::ACCOUNT_ID:mfa/handbook-admin \
  --authentication-code1 123456 --authentication-code2 789012
```

---

## 7. Inspection & cleanup

```bash
aws iam list-attached-user-policies --user-name handbook-deploy
aws iam list-user-policies --user-name handbook-deploy
aws iam get-policy-version \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess \
  --version-id v1

# Detach and delete (lab teardown)
aws iam detach-user-policy --user-name handbook-deploy \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess
aws iam delete-user --user-name handbook-deploy
```

**DevOps note:** CI uses **OIDC** (`AssumeRoleWithWebIdentity`) instead of static keys—same role model, different trust principal.

---

## 8. Lab — Day 2

1. Create group `handbook-devs` with `ReadOnlyAccess`.
2. Create user `handbook-deploy`; add to group; **do not** attach PowerUser in prod patterns.
3. Write and attach custom S3 policy from section 4.
4. Create role `EC2-S3-ReadRole` + instance profile.
5. Run `simulate-principal-policy` for allowed and denied actions.
6. Delete access keys if created; keep user for later days or delete per teardown list.

**Next:** [Day 3 — EC2 instances & AMIs](../day3/)
