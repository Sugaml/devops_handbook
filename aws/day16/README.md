# Day 16 — SNS & SQS Messaging

**Goal:** Wire pub/sub notifications and decouple services with queues, DLQs, and CLI-driven workflows.

**Time:** 4–5 hours

**Services:** SNS, SQS

---

## 1. SNS topic

```bash
TOPIC_ARN=$(aws sns create-topic --name handbook-events --query TopicArn --output text)
aws sns subscribe --topic-arn "$TOPIC_ARN" --protocol email --notification-endpoint you@example.com
# Confirm via email link

aws sns publish --topic-arn "$TOPIC_ARN" --message "deploy completed" --subject "Handbook Lab"
```

---

## 2. SQS standard queue

```bash
QUEUE_URL=$(aws sqs create-queue --queue-name handbook-jobs \
  --attributes VisibilityTimeout=30,MessageRetentionPeriod=86400 \
  --query QueueUrl --output text)

aws sqs send-message --queue-url "$QUEUE_URL" --message-body '{"job":"process-order","id":1}'
aws sqs receive-message --queue-url "$QUEUE_URL" --wait-time-seconds 10
aws sqs delete-message --queue-url "$QUEUE_URL" --receipt-handle "RECEIPT_HANDLE"
```

---

## 3. Dead-letter queue

```bash
DLQ_URL=$(aws sqs create-queue --queue-name handbook-jobs-dlq --query QueueUrl --output text)
DLQ_ARN=$(aws sqs get-queue-attributes --queue-url "$DLQ_URL" --attribute-names QueueArn \
  --query Attributes.QueueArn --output text)

aws sqs set-queue-attributes --queue-url "$QUEUE_URL" \
  --attributes '{"RedrivePolicy":"{\"deadLetterTargetArn\":\"'"$DLQ_ARN"'\",\"maxReceiveCount\":\"3\"}"}'
```

---

## 4. SNS → SQS fan-out

```bash
aws sns subscribe --topic-arn "$TOPIC_ARN" --protocol sqs --notification-endpoint "$DLQ_ARN" \
  --attributes RawMessageDelivery=true
# Queue policy must allow SNS — use aws sns subscribe which often sets policy
```

---

## 5. Lab — Day 16

1. Email subscription to SNS; publish test alert.
2. Producer script sends 10 messages to SQS; consumer script processes and deletes.
3. Configure DLQ; force failures (bad handler) until message lands in DLQ.
4. Purge queues and delete resources.

**Previous:** [Day 15](../day15/) · **Next:** [Day 17 — RDS](../day17/)
