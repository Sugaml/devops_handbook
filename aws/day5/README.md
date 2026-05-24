# Day 5 — S3: Buckets, Objects & Policies

**Goal:** Create buckets, upload/sync objects, enable versioning, and apply bucket policies and public-access blocks.

**Time:** 4–5 hours

**Services:** S3

---

## 1. Bucket lifecycle

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET="devops-handbook-${ACCOUNT_ID}-us-east-1"

aws s3api create-bucket --bucket "$BUCKET" --region us-east-1
# us-west-2 requires LocationConstraint:
# aws s3api create-bucket --bucket "$BUCKET" --region us-west-2 \
#   --create-bucket-configuration LocationConstraint=us-west-2

aws s3api list-buckets --query 'Buckets[].Name' --output table
aws s3api get-bucket-location --bucket "$BUCKET"
```

Block public access (default best practice):

```bash
aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

---

## 2. Objects — high-level CLI

```bash
echo "hello handbook" > /tmp/hello.txt
aws s3 cp /tmp/hello.txt "s3://${BUCKET}/docs/hello.txt"
aws s3 ls "s3://${BUCKET}/"
aws s3 ls "s3://${BUCKET}/docs/" --human-readable --summarize

aws s3 sync ./local-dir "s3://${BUCKET}/backup/" --delete
aws s3 mv "s3://${BUCKET}/docs/hello.txt" "s3://${BUCKET}/archive/hello.txt"
aws s3 rm "s3://${BUCKET}/archive/hello.txt"
aws s3 presign "s3://${BUCKET}/docs/hello.txt" --expires-in 3600
```

---

## 3. API-level operations

```bash
aws s3api put-object --bucket "$BUCKET" --key config/app.json \
  --body app.json --content-type application/json

aws s3api head-object --bucket "$BUCKET" --key config/app.json
aws s3api get-object --bucket "$BUCKET" --key config/app.json /tmp/out.json

# Versioning
aws s3api put-bucket-versioning --bucket "$BUCKET" \
  --versioning-configuration Status=Enabled
aws s3api list-object-versions --bucket "$BUCKET" --prefix config/
```

---

## 4. Encryption

```bash
aws s3api put-bucket-encryption --bucket "$BUCKET" \
  --server-side-encryption-configuration '{
    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
  }'

# SSE-KMS (Day 23)
aws s3 cp file.txt "s3://${BUCKET}/" --sse aws:kms --sse-kms-key-id alias/handbook
```

---

## 5. Bucket policy example

`bucket-policy.json` — allow read from specific role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowRoleRead",
      "Effect": "Allow",
      "Principal": { "AWS": "arn:aws:iam::ACCOUNT_ID:role/EC2-S3-ReadRole" },
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::BUCKET_NAME",
        "arn:aws:s3:::BUCKET_NAME/*"
      ]
    }
  ]
}
```

```bash
aws s3api put-bucket-policy --bucket "$BUCKET" --policy file://bucket-policy.json
aws s3api get-bucket-policy --bucket "$BUCKET"
```

---

## 6. Lab — Day 5

1. Create bucket with account ID suffix; enable versioning.
2. Sync a local folder; list with `--summarize`.
3. Overwrite a file twice; list versions; delete specific version.
4. Generate presigned URL; download with `curl`.
5. Empty bucket and delete: `aws s3 rb s3://$BUCKET --force`

**Previous:** [Day 4](../day4/) · **Next:** [Day 6 — Query & pagination](../day6/)
