# Day 4 — EC2 Networking: Security Groups, EIPs & Metadata

**Goal:** Master security group rules, elastic IPs, ENIs, and IMDSv2 for instance introspection.

**Time:** 4–5 hours

**Services:** EC2, VPC (default VPC)

---

## 1. Security groups deep dive

Stateful firewall at ENI level—**allow only** (no Deny rules).

```bash
SG_ID=$(aws ec2 describe-security-groups --filters Name=group-name,Values=handbook-sg \
  --query 'SecurityGroups[0].GroupId' --output text)

# Ingress: HTTP from anywhere (lab only)
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" --protocol tcp --port 80 --cidr 0.0.0.0/0

# Ingress referencing another SG (app ← load balancer)
aws ec2 authorize-security-group-ingress \
  --group-id "$APP_SG" --protocol tcp --port 8080 \
  --source-group "$ALB_SG"

# List rules
aws ec2 describe-security-groups --group-ids "$SG_ID" \
  --query 'SecurityGroups[0].{Ingress:IpPermissions,Egress:IpPermissionsEgress}'

# Revoke rule
aws ec2 revoke-security-group-ingress \
  --group-id "$SG_ID" --protocol tcp --port 80 --cidr 0.0.0.0/0
```

| vs NACL | Security group |
|---------|----------------|
| Stateless | Stateful |
| Subnet level | ENI level |
| Allow + Deny | Allow only |

---

## 2. Elastic IP

```bash
ALLOC_ID=$(aws ec2 allocate-address --domain vpc --query AllocationId --output text)
aws ec2 associate-address --instance-id "$INSTANCE_ID" --allocation-id "$ALLOC_ID"

aws ec2 describe-addresses --allocation-ids "$ALLOC_ID"

# Release when done (charges if not attached)
aws ec2 disassociate-address --association-id ...
aws ec2 release-address --allocation-id "$ALLOC_ID"
```

---

## 3. ENIs and multiple IPs

```bash
aws ec2 describe-network-interfaces --filters Name=attachment.instance-id,Values="$INSTANCE_ID"
aws ec2 create-network-interface --subnet-id subnet-xxx --groups "$SG_ID"
```

---

## 4. Instance metadata (IMDSv2)

From **inside** the instance:

```bash
TOKEN=$(curl -sX PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
curl -sH "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/instance-id
curl -sH "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

Require IMDSv2 on new launches:

```bash
aws ec2 run-instances ... \
  --metadata-options HttpTokens=required,HttpEndpoint=enabled
```

**DevOps note:** SSRF attacks steal creds from IMDSv1—enforce v2 account-wide with a config rule.

---

## 5. Reachability checks

```bash
aws ec2 describe-instance-connect-endpoints  # optional feature
aws ec2-instance-connect send-ssh-public-key \
  --instance-id "$INSTANCE_ID" \
  --instance-os-user ec2-user \
  --ssh-public-key file://~/.ssh/id_rsa.pub \
  --availability-zone us-east-1a
```

---

## 6. Lab — Day 4

1. Launch instance in default VPC; attach Elastic IP; SSH via EIP.
2. Open port 80; serve static page; test from laptop `curl http://EIP`.
3. From instance, fetch role creds via IMDSv2 (after attaching instance profile from Day 2).
4. Revoke 0.0.0.0/0 on port 80; restrict SSH to your IP only.
5. Release EIP; terminate instance.

**Previous:** [Day 3](../day3/) · **Next:** [Day 5 — S3](../day5/)
