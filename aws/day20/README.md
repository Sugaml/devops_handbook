# Day 20 — API Gateway (REST)

**Goal:** Expose Lambda via REST API, deploy stages, and test with curl.

**Time:** 4–5 hours

**Services:** API Gateway, Lambda

---

## 1. HTTP API vs REST API

| | HTTP API | REST API |
|---|----------|----------|
| Cost | Lower | Higher features |
| Use | Simple proxies | API keys, request validation |

This day uses **REST API** for classic DevOps interviews.

---

## 2. Create API and resource

```bash
API_ID=$(aws apigateway create-rest-api --name handbook-api \
  --endpoint-configuration types=REGIONAL \
  --query id --output text)
ROOT_ID=$(aws apigateway get-resources --rest-api-id "$API_ID" \
  --query 'items[?path==`/`].id' --output text)
RESOURCE_ID=$(aws apigateway create-resource --rest-api-id "$API_ID" \
  --parent-id "$ROOT_ID" --path-part hello --query id --output text)
```

---

## 3. Method, integration, deployment

```bash
aws apigateway put-method --rest-api-id "$API_ID" --resource-id "$RESOURCE_ID" \
  --http-method GET --authorization-type NONE

aws apigateway put-integration --rest-api-id "$API_ID" --resource-id "$RESOURCE_ID" \
  --http-method GET --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:ACCOUNT_ID:function:handbook-hello/invocations

aws lambda add-permission --function-name handbook-hello \
  --statement-id apigateway-invoke --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:ACCOUNT_ID:${API_ID}/*/*"

aws apigateway create-deployment --rest-api-id "$API_ID" --stage-name prod
```

Invoke URL: `https://${API_ID}.execute-api.us-east-1.amazonaws.com/prod/hello`

```bash
curl -s "https://${API_ID}.execute-api.us-east-1.amazonaws.com/prod/hello" | jq .
```

---

## 4. Lab — Day 20

1. Connect Day 19 Lambda to GET `/hello`.
2. Add POST `/echo` with mapping template (optional).
3. Enable CloudWatch logging on API stage.
4. Delete API, deployment, Lambda permission.

**Previous:** [Day 19](../day19/) · **Next:** [Day 21 — ECS](../day21/)
