# Day 19 — Lambda: Serverless Functions

**Goal:** Deploy Lambda functions, configure IAM roles, triggers, versions, and aliases.

**Time:** 5–6 hours

**Services:** Lambda, IAM, CloudWatch Logs

---

## 1. Execution role

```bash
aws iam create-role --role-name HandbookLambdaRole \
  --assume-role-policy-document '{
    "Version":"2012-10-17",
    "Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]
  }'
aws iam attach-role-policy --role-name HandbookLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

---

## 2. Package and create function

`handler.py`:

```python
import json
def handler(event, context):
    return {"statusCode": 200, "body": json.dumps({"message": "hello handbook"})}
```

```bash
zip function.zip handler.py
aws lambda create-function \
  --function-name handbook-hello \
  --runtime python3.12 \
  --role arn:aws:iam::ACCOUNT_ID:role/HandbookLambdaRole \
  --handler handler.handler \
  --zip-file fileb://function.zip \
  --timeout 10 --memory-size 128 \
  --tags Project=devops-handbook

aws lambda invoke --function-name handbook-hello /tmp/out.json && cat /tmp/out.json
```

---

## 3. Update code & publish version

```bash
aws lambda update-function-code --function-name handbook-hello --zip-file fileb://function.zip
aws lambda publish-version --function-name handbook-hello
aws lambda create-alias --function-name handbook-hello --name live --function-version 1
```

---

## 4. Event source (SQS example)

```bash
aws lambda create-event-source-mapping \
  --function-name handbook-hello \
  --event-source-arn "$QUEUE_ARN" \
  --batch-size 10
```

---

## 5. Environment variables & secrets

```bash
aws lambda update-function-configuration \
  --function-name handbook-hello \
  --environment Variables={ENV=lab}
# Secrets: reference Secrets Manager ARN in env or use extension
```

---

## 6. Lab — Day 19

1. Deploy Python Lambda returning JSON.
2. Add CloudWatch Logs tail; invoke 20 times.
3. Wire SQS queue from Day 16 as trigger.
4. Delete event source mapping, function, role.

**Previous:** [Day 18](../day18/) · **Next:** [Day 20 — API Gateway](../day20/)
