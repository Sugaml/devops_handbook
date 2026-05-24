# Day 13 — Route 53: DNS Zones & Records

**Goal:** Create hosted zones, manage record sets, and use health checks for failover patterns.

**Time:** 4–5 hours

**Services:** Route 53

---

## 1. Public hosted zone

```bash
# Requires a domain you control in registrar
aws route53 create-hosted-zone --name lab.example.com --caller-reference "handbook-$(date +%s)"
ZONE_ID=$(aws route53 list-hosted-zones-by-name --dns-name lab.example.com \
  --query 'HostedZones[0].Id' --output text | sed 's|/hostedzone/||')

aws route53 get-hosted-zone --id "$ZONE_ID"
```

Update registrar NS records to the four nameservers Route 53 returns.

---

## 2. Record sets

`change-batch.json`:

```json
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "www.lab.example.com",
      "Type": "A",
      "TTL": 300,
      "ResourceRecords": [{ "Value": "203.0.113.10" }]
    }
  }]
}
```

```bash
aws route53 change-resource-record-sets --hosted-zone-id "$ZONE_ID" \
  --change-batch file://change-batch.json

# Alias to ALB (no TTL — evaluated target health)
aws route53 change-resource-record-sets --hosted-zone-id "$ZONE_ID" --change-batch '{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "app.lab.example.com",
      "Type": "A",
      "AliasTarget": {
        "HostedZoneId": "Z35SXDOTRQ7X7K",
        "DNSName": "dualstack.my-alb-123.us-east-1.elb.amazonaws.com",
        "EvaluateTargetHealth": true
      }
    }
  }]
}'
```

---

## 3. Health checks

```bash
aws route53 create-health-check \
  --health-check-config IPAddress=203.0.113.10,Port=80,Type=HTTP,ResourcePath=/,RequestInterval=30,FailureThreshold=3
```

---

## 4. Lab — Day 13

1. Create hosted zone (or use `example.com` private zone in VPC for internal-only lab).
2. Add `A` record pointing to Day 10 ALB via alias.
3. `dig` / `nslookup` verify resolution.
4. Delete test records; delete zone if disposable.

**Previous:** [Day 12](../day12/) · **Next:** [Day 14 — CloudWatch metrics](../day14/)
