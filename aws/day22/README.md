# Day 22 — Secrets Manager & Systems Manager Parameter Store

**Goal:** Store and rotate secrets; use hierarchical parameters for config; reference from Lambda/ECS.

**Time:** 4–5 hours

**Services:** Secrets Manager, SSM

---

## 1. Secrets Manager

```bash
aws secretsmanager create-secret \
  --name handbook/db/password \
  --secret-string '{"username":"dbadmin","password":"REPLACE_WITH_STRONG"}'

aws secretsmanager get-secret-value --secret-id handbook/db/password \
  --query SecretString --output text | jq .

aws secretsmanager rotate-secret --secret-id handbook/db/password \
  --rotation-lambda-arn arn:aws:lambda:...  # requires rotation function
```

---

## 2. Parameter Store

```bash
aws ssm put-parameter --name /handbook/app/log-level --value info --type String
aws ssm put-parameter --name /handbook/app/api-key --value "secret-value" --type SecureString

aws ssm get-parameter --name /handbook/app/log-level --query Parameter.Value
aws ssm get-parameter --name /handbook/app/api-key --with-decryption

aws ssm get-parameters-by-path --path /handbook/app --recursive
```

---

## 3. IAM for read access

```json
{
  "Effect": "Allow",
  "Action": ["secretsmanager:GetSecretValue"],
  "Resource": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:handbook/*"
}
```

ECS task execution role needs `secretsmanager:GetSecretValue` for secret injection in task definition.

---

## 4. Lab — Day 22

1. Store RDS password in Secrets Manager (Day 17).
2. Mirror non-secret config in Parameter Store hierarchy.
3. Lambda (Day 19) reads parameter at cold start (extend handler).
4. Delete secrets and parameters after lab.

**Previous:** [Day 21](../day21/) · **Next:** [Day 23 — KMS](../day23/)
