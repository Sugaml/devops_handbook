# Day 14 — CloudWatch Metrics, Alarms & Dashboards

**Goal:** Publish custom metrics, create alarms, and build dashboards for EC2/ALB observability.

**Time:** 4–5 hours

**Services:** CloudWatch

---

## 1. Explore built-in metrics

```bash
aws cloudwatch list-metrics --namespace AWS/EC2 --dimensions Name=InstanceId,Value="$INSTANCE_ID"
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value="$INSTANCE_ID" \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S 2>/dev/null || date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 --statistics Average
```

---

## 2. Custom metric

```bash
aws cloudwatch put-metric-data \
  --namespace DevOpsHandbook \
  --metric-data MetricName=JobsProcessed,Value=42,Unit=Count,Dimensions=[{Name=Environment,Value=lab}]
```

---

## 3. Alarms

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name handbook-high-cpu \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average --period 300 --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=InstanceId,Value="$INSTANCE_ID" \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:handbook-alerts
```

---

## 4. Dashboard

`dashboard.json`:

```json
{
  "widgets": [{
    "type": "metric",
    "x": 0, "y": 0, "width": 12, "height": 6,
    "properties": {
      "metrics": [["AWS/EC2", "CPUUtilization", "InstanceId", "i-xxx"]],
      "period": 300,
      "stat": "Average",
      "region": "us-east-1",
      "title": "EC2 CPU"
    }
  }]
}
```

```bash
aws cloudwatch put-dashboard --dashboard-name Handbook \
  --dashboard-body file://dashboard.json
```

---

## 5. Lab — Day 14

1. Create SNS topic `handbook-alerts`; subscribe your email; confirm subscription.
2. Alarm on EC2 CPU > 70% for 10 minutes; trigger with `stress` tool.
3. Publish custom metric from a script every minute.
4. Build dashboard with EC2 CPU + ALB request count.

**Previous:** [Day 13](../day13/) · **Next:** [Day 15 — CloudWatch Logs](../day15/)
