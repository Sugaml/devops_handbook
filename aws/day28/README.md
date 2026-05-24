# Day 28 — WAF, Network Security & Guardrails

**Goal:** Attach AWS WAF to ALB, review security posture, and apply Config-style guardrails concepts.

**Time:** 4–5 hours

**Services:** WAFv2, Shield (awareness), EC2, AWS Config (intro)

---

## 1. Web ACL

```bash
WEB_ACL_ARN=$(aws wafv2 create-web-acl \
  --name handbook-waf \
  --scope REGIONAL \
  --default-action Allow={} \
  --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=handbook-waf \
  --region us-east-1 \
  --query Summary.ARN --output text)
```

---

## 2. Managed rule groups

```bash
aws wafv2 update-web-acl --name handbook-waf --scope REGIONAL \
  --id ... --lock-token ... \
  --default-action Allow={} \
  --rules '[{
    "Name": "AWS-AWSManagedRulesCommonRuleSet",
    "Priority": 1,
    "Statement": {
      "ManagedRuleGroupStatement": {
        "VendorName": "AWS",
        "Name": "AWSManagedRulesCommonRuleSet"
      }
    },
    "OverrideAction": {"None": {}},
    "VisibilityConfig": {
      "SampledRequestsEnabled": true,
      "CloudWatchMetricsEnabled": true,
      "MetricName": "common"
    }
  }]' \
  --visibility-config ...
```

Associate with ALB:

```bash
aws wafv2 associate-web-acl --web-acl-arn "$WEB_ACL_ARN" \
  --resource-arn "$ALB_ARN"
```

---

## 3. Rate-based rule

Block IPs exceeding 2000 requests / 5 min (lab tuning):

```bash
# Add RateBasedStatement to web ACL rules array
```

---

## 4. Security audit CLI checklist

```bash
# Open port 22 to 0.0.0.0/0
aws ec2 describe-security-groups \
  --filters Name=ip-permission.cidr,Values=0.0.0.0/0 \
  --query 'SecurityGroups[?IpPermissions[?ToPort==`22`]]'

# Public S3 buckets
aws s3api list-buckets --query 'Buckets[].Name' --output text | while read b; do
  aws s3api get-bucket-policy-status --bucket "$b" 2>/dev/null
done

# IAM access key age
aws iam generate-credential-report
aws iam get-credential-report --query 'Content' --output text | base64 -d | csvcut -c user,access_key_1_last_rotated
```

---

## 5. AWS Config (intro)

```bash
aws configservice describe-configuration-recorders
# Enable recorder + managed rule IAM_PASSWORD_POLICY in production accounts
```

---

## 6. Lab — Day 28

1. Associate WAF with Day 10 ALB; run SQLi test string; verify blocked in sampled requests.
2. Run security group audit script; fix overly permissive rules.
3. Document Shield Standard vs Advanced (DDoS).
4. Disassociate and delete Web ACL.

**Previous:** [Day 27](../day27/) · **Next:** [Day 29 — Cost & tagging](../day29/)
