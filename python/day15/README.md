# Day 15 — boto3 AWS Automation (EC2, S3, STS)

**Goal:** Use boto3 to verify AWS identity with STS, list and tag EC2 instances, and perform common S3 operations — the foundation for inventory scripts, cost reports, and deploy automation.

**Time:** 5–6 hours (theory + hands-on)

**Services:** STS, EC2, S3

---

## 1. boto3 architecture

```
  Python script
       │
       ▼
  boto3 client/resource  ──►  AWS API (HTTPS)
       │
       └── Credentials from env, ~/.aws/credentials, or IAM role
```

| API style | Use when |
|-----------|----------|
| **Client** | Low-level; full API surface; returns dicts |
| **Resource** | Higher-level ORM for EC2, S3 objects |

```bash
pip install boto3
export AWS_PROFILE=devops-handbook   # from AWS handbook Day 1
export AWS_REGION=us-east-1
```

---

## 2. STS — who am I?

Always start automation with identity verification:

```python
import boto3

sts = boto3.client("sts")
identity = sts.get_caller_identity()
print(identity["Account"], identity["Arn"])
```

Catches wrong profile, expired session token, or missing permissions before mutating resources.

---

## 3. EC2 — list and filter instances

```python
ec2 = boto3.client("ec2")

resp = ec2.describe_instances(
    Filters=[
        {"Name": "instance-state-name", "Values": ["running"]},
        {"Name": "tag:Project", "Values": ["devops-handbook"]},
    ]
)

for reservation in resp["Reservations"]:
    for inst in reservation["Instances"]:
        name = next(
            (t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"),
            inst["InstanceId"],
        )
        print(name, inst["InstanceId"], inst["InstanceType"])
```

**Pagination:** Large accounts need paginators:

```python
paginator = ec2.get_paginator("describe_instances")
for page in paginator.paginate(Filters=[...]):
    ...
```

---

## 4. EC2 — tag and stop (with guardrails)

```python
def tag_instance(ec2, instance_id: str, tags: dict[str, str]) -> None:
    ec2.create_tags(
        Resources=[instance_id],
        Tags=[{"Key": k, "Value": v} for k, v in tags.items()],
    )

def stop_instance(ec2, instance_id: str, dry_run: bool = True) -> None:
    ec2.stop_instances(InstanceIds=[instance_id], DryRun=dry_run)
```

Use `DryRun=True` first — AWS returns `DryRunOperation` if you would succeed, `UnauthorizedOperation` if not.

---

## 5. S3 — list buckets and objects

```python
s3 = boto3.client("s3")

buckets = s3.list_buckets()
for b in buckets["Buckets"]:
    print(b["Name"], b["CreationDate"])

# List prefix
resp = s3.list_objects_v2(Bucket="my-bucket", Prefix="logs/", MaxKeys=100)
for obj in resp.get("Contents", []):
    print(obj["Key"], obj["Size"])
```

---

## 6. S3 — upload and download

```python
# Upload file
s3.upload_file("/tmp/report.json", "my-bucket", "reports/2026/report.json")

# Download
s3.download_file("my-bucket", "reports/2026/report.json", "/tmp/report.json")

# In-memory
import io
buf = io.BytesIO()
s3.download_fileobj("my-bucket", "key", buf)
```

For large files, use **transfer config** with multipart thresholds.

---

## 7. Error handling

```python
from botocore.exceptions import ClientError

try:
    s3.head_bucket(Bucket="nonexistent-bucket-xyz")
except ClientError as exc:
    code = exc.response["Error"]["Code"]
    if code == "404":
        print("Bucket not found")
    else:
        raise
```

| Code | Meaning |
|------|---------|
| `AccessDenied` | IAM policy missing action |
| `UnauthorizedOperation` | Dry-run would fail |
| `InvalidInstanceID.NotFound` | Wrong instance ID |

---

## 8. Session and profiles

```python
import boto3

session = boto3.Session(profile_name="devops-handbook", region_name="us-east-1")
ec2 = session.client("ec2")
```

Multi-account tools assume a role per account:

```python
def client_with_role(service: str, role_arn: str, session_name: str = "handbook"):
    sts = boto3.client("sts")
    creds = sts.assume_role(RoleArn=role_arn, RoleSessionName=session_name)["Credentials"]
    return boto3.client(
        service,
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
    )
```

---

## 9. Lab — Day 15

Work from `python/day15/labs/`. Requires configured AWS credentials (AWS handbook Day 1).

1. Run `python aws_inventory.py identity` — print account ID and ARN.
2. Run `python aws_inventory.py ec2 --state running` — table of instances (may be empty in new accounts).
3. Run `python aws_inventory.py s3` — list bucket names.
4. Create a test bucket (if allowed), run `python aws_inventory.py s3-upload /tmp/test.txt my-bucket/handbook/test.txt`.
5. Run EC2 tag command with `--dry-run` on a known instance ID.
6. Intentionally use wrong profile; confirm STS failure message is clear.

**Stretch:** Export inventory as JSON for Ansible dynamic inventory input.

---

## 10. DevOps connections

- **Terraform:** Creates resources; boto3 scripts audit drift, enforce tags, or emergency stop.
- **CI/CD:** Deploy jobs assume OIDC roles — same STS patterns, different credential source.
- **Cost optimization:** Scheduled boto3 reports find unattached EBS volumes and old snapshots.

---

## Quick reference

| Task | boto3 call |
|------|------------|
| Who am I? | `sts.get_caller_identity()` |
| List EC2 | `ec2.describe_instances(Filters=[...])` |
| Tag EC2 | `ec2.create_tags(...)` |
| List buckets | `s3.list_buckets()` |
| Upload file | `s3.upload_file(local, bucket, key)` |
| Dry run stop | `ec2.stop_instances(..., DryRun=True)` |

**Next:** [Day 16 — Docker automation](../day16/)
