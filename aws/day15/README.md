# Day 15 — CloudWatch Logs & Insights

**Goal:** Create log groups, stream application logs, use metric filters, and query with Logs Insights.

**Time:** 4–5 hours

**Services:** CloudWatch Logs

---

## 1. Log groups and streams

```bash
aws logs create-log-group --log-group-name /handbook/app
aws logs create-log-stream --log-group-name /handbook/app --log-stream-name instance-1

aws logs put-log-events --log-group-name /handbook/app --log-stream-name instance-1 \
  --log-events timestamp=$(($(date +%s)*1000)),message="application started"
```

---

## 2. Agent / unified CloudWatch agent (concept)

On EC2, IAM role needs `CloudWatchAgentServerPolicy`. Config via SSM parameter—production standard.

```bash
aws logs describe-log-groups --log-group-name-prefix /handbook
aws logs tail /handbook/app --follow   # CLI v2 convenience
```

---

## 3. Metric filter

```bash
aws logs put-metric-filter \
  --log-group-name /handbook/app \
  --filter-name ErrorCount \
  --filter-pattern "?ERROR ?Error ?error" \
  --metric-transformations \
    metricName=AppErrors,metricNamespace=DevOpsHandbook,metricValue=1
```

---

## 4. Logs Insights query

```bash
aws logs start-query \
  --log-group-name /handbook/app \
  --start-time $(($(date +%s)-3600)) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20'

QUERY_ID=...
aws logs get-query-results --query-id "$QUERY_ID"
```

---

## 5. Subscription to Lambda (pattern)

Export logs to S3 or stream to Lambda for alerting—use `put-subscription-filter` in advanced labs.

---

## 6. Lab — Day 15

1. Create log group; push 20 events via CLI and script loop.
2. Create metric filter for `ERROR`; generate errors; verify metric in CloudWatch.
3. Run Insights query for top 10 messages by count.
4. Set retention to 7 days on log group.

**Previous:** [Day 14](../day14/) · **Next:** [Day 16 — SNS & SQS](../day16/)
