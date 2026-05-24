# Day 18 — DynamoDB: NoSQL Tables & Operations

**Goal:** Create tables with on-demand billing, CRUD items, query GSI/LSI, and enable point-in-time recovery.

**Time:** 4–5 hours

**Services:** DynamoDB

---

## 1. Create table

```bash
aws dynamodb create-table \
  --table-name handbook-orders \
  --attribute-definitions \
    AttributeName=pk,AttributeType=S \
    AttributeName=sk,AttributeType=S \
    AttributeName=gsi1pk,AttributeType=S \
  --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE \
  --global-secondary-indexes '[
    {
      "IndexName": "gsi1",
      "KeySchema": [{"AttributeName":"gsi1pk","KeyType":"HASH"}],
      "Projection": {"ProjectionType":"ALL"}
    }
  ]' \
  --billing-mode PAY_PER_REQUEST \
  --tags Key=Project,Value=devops-handbook

aws dynamodb wait table-exists --table-name handbook-orders
```

---

## 2. Put, get, query

```bash
aws dynamodb put-item --table-name handbook-orders --item '{
  "pk": {"S": "USER#alice"},
  "sk": {"S": "ORDER#1001"},
  "gsi1pk": {"S": "STATUS#OPEN"},
  "amount": {"N": "49.99"}
}'

aws dynamodb get-item --table-name handbook-orders --key \
  '{"pk":{"S":"USER#alice"},"sk":{"S":"ORDER#1001"}}'

aws dynamodb query --table-name handbook-orders \
  --key-condition-expression "pk = :pk" \
  --expression-attribute-values '{":pk":{"S":"USER#alice"}}'
```

---

## 3. Batch and scan (use sparingly)

```bash
aws dynamodb scan --table-name handbook-orders --max-items 10
# Prefer Query over Scan in production
```

---

## 4. Backup & PITR

```bash
aws dynamodb update-continuous-backups \
  --table-name handbook-orders \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

aws dynamodb create-backup --table-name handbook-orders \
  --backup-name handbook-orders-backup-$(date +%Y%m%d)
```

---

## 5. Lab — Day 18

1. Single-table design: users and orders with composite keys.
2. Query open orders via GSI.
3. Enable PITR; delete table item; discuss recovery options.
4. Delete table when done.

**Previous:** [Day 17](../day17/) · **Next:** [Day 19 — Lambda](../day19/)
