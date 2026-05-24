# Day 23 — KMS: Encryption Keys & Policies

**Goal:** Create CMKs, encrypt/decrypt data, use aliases, and enforce encryption on S3/RDS/EBS.

**Time:** 4–5 hours

**Services:** KMS

---

## 1. Customer managed key

```bash
KEY_ID=$(aws kms create-key --description "handbook lab key" \
  --query KeyMetadata.KeyId --output text)
aws kms create-alias --alias-name alias/handbook --target-key-id "$KEY_ID"

aws kms list-aliases --query 'Aliases[?starts_with(AliasName,`alias/handbook`)]'
```

---

## 2. Encrypt / decrypt

```bash
aws kms encrypt --key-id alias/handbook --plaintext "sensitive data" \
  --query CiphertextBlob --output text | base64 -d > /tmp/blob.bin

aws kms decrypt --ciphertext-blob fileb:///tmp/blob.bin \
  --query Plaintext --output text | base64 -d
```

---

## 3. Key policy (cross-account pattern)

```bash
aws kms get-key-policy --key-id "$KEY_ID" --policy-name default --output text | jq .
# Grant specific role: kms:Decrypt on key
```

---

## 4. Service integration

```bash
# S3 bucket default encryption with CMK
aws s3api put-bucket-encryption --bucket "$BUCKET" \
  --server-side-encryption-configuration '{
    "Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"aws:kms","KMSMasterKeyID":"alias/handbook"}}]
  }'

# EBS encrypted volume
aws ec2 create-volume --size 10 --availability-zone "$AZ" \
  --encrypted --kms-key-id alias/handbook
```

---

## 5. Lab — Day 23

1. Create CMK + alias.
2. Encrypt file with CLI; decrypt and verify.
3. S3 object upload with SSE-KMS.
4. Schedule key deletion (7–30 day waiting period)—use dedicated lab key only.

**Previous:** [Day 22](../day22/) · **Next:** [Day 24 — CloudFormation](../day24/)
