# Day 10 — Elastic Load Balancing (ALB & NLB)

**Goal:** Create an Application Load Balancer, target group, listeners, and health checks; register EC2 targets.

**Time:** 5–6 hours

**Services:** ELBv2, EC2, ACM (optional HTTPS)

---

## 1. Target group

```bash
TG_ARN=$(aws elbv2 create-target-group \
  --name handbook-tg \
  --protocol HTTP --port 80 \
  --vpc-id "$VPC_ID" \
  --health-check-path / \
  --matcher HttpCode=200 \
  --query 'TargetGroups[0].TargetGroupArn' --output text)
```

---

## 2. Application Load Balancer

```bash
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name handbook-alb \
  --type application \
  --subnets "$SUBNET_PUB1" "$SUBNET_PUB2" \
  --security-groups "$SG_ID" \
  --scheme internet-facing \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text)

aws elbv2 create-listener \
  --load-balancer-arn "$ALB_ARN" \
  --protocol HTTP --port 80 \
  --default-actions Type=forward,TargetGroupArn="$TG_ARN"
```

---

## 3. Register targets

```bash
aws elbv2 register-targets --target-group-arn "$TG_ARN" \
  --targets Id="$INSTANCE_ID"
aws elbv2 describe-target-health --target-group-arn "$TG_ARN"
```

---

## 4. HTTPS listener (optional)

```bash
# Request cert in ACM (must validate DNS)
CERT_ARN=$(aws acm request-certificate --domain-name lab.example.com \
  --validation-method DNS --query CertificateArn --output text)

aws elbv2 create-listener \
  --load-balancer-arn "$ALB_ARN" \
  --protocol HTTPS --port 443 \
  --certificates CertificateArn="$CERT_ARN" \
  --default-actions Type=forward,TargetGroupArn="$TG_ARN"
```

| Type | Layer | Use case |
|------|-------|----------|
| ALB | 7 | HTTP routing, host/path rules |
| NLB | 4 | TCP/UDP, static IP, extreme perf |
| GLB | 3/4 | Gateway Load Balancer — appliances |

---

## 5. Lab — Day 10

1. Two EC2 instances with nginx on port 80 in public subnets.
2. Create ALB + target group; verify both healthy.
3. Hit ALB DNS name; stop one instance; observe health check failure.
4. Add path-based rule `/api/*` to second target group (optional).
5. Delete listener, ALB, target group; terminate instances.

**Previous:** [Day 9](../day9/) · **Next:** [Day 11 — Auto Scaling](../day11/)
