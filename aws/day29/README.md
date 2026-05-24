# Day 29 — Tagging, Cost Explorer & Budgets

**Goal:** Enforce tagging discipline, analyze spend with CLI, and create budgets with alerts.

**Time:** 4–5 hours

**Services:** Resource Groups Tagging API, Cost Explorer, Budgets, Organizations (read-only)

---

## 1. Tagging resources

```bash
aws ec2 create-tags --resources "$INSTANCE_ID" \
  --tags Key=Project,Value=devops-handbook Key=Owner,Value=you Key=Environment,Value=lab

# Tag on create (preferred)
--tag-specifications 'ResourceType=instance,Tags=[{Key=Project,Value=devops-handbook}]'
```

---

## 2. Resource Explorer / tag API

```bash
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=devops-handbook \
  --query 'ResourceTagMappingList[].ResourceARN' --output table

aws resourcegroupstaggingapi tag-resources \
  --resource-arn-list "arn:aws:s3:::my-bucket" \
  --tags Project=devops-handbook
```

---

## 3. Cost Explorer (enable in console once per account)

```bash
aws ce get-cost-and-usage \
  --time-period Start=2026-05-01,End=2026-05-24 \
  --granularity DAILY \
  --metrics UnblendedCost \
  --group-by Type=TAG,Key=Project

aws ce get-cost-and-usage \
  --time-period Start=2026-05-01,End=2026-05-24 \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --filter '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Elastic Compute Cloud - Compute"]}}'
```

---

## 4. Budgets

```bash
aws budgets create-budget \
  --account-id "$ACCOUNT_ID" \
  --budget '{
    "BudgetName": "handbook-monthly",
    "BudgetLimit": {"Amount": "20", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers '[{
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80
    },
    "Subscribers": [{"SubscriptionType": "EMAIL", "Address": "you@example.com"}]
  }]'
```

---

## 5. Cost allocation tags

Activate user-defined tags in Billing console (`Project`, `Environment`) so Cost Explorer groups correctly.

---

## 6. Lab — Day 29

1. Tag all remaining handbook resources consistently.
2. Report last 7 days cost grouped by service.
3. Create $20 monthly budget with 80% email alert.
4. Write team tagging policy (5 required keys) in your notes.

**Previous:** [Day 28](../day28/) · **Next:** [Day 30 — Production & multi-account](../day30/)
