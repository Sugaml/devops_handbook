# Day 21 — ECS & ECR: Containers on AWS

**Goal:** Push an image to ECR, run Fargate tasks, and operate an ECS service behind a load balancer.

**Time:** 6–8 hours

**Services:** ECR, ECS, ELBv2, IAM

---

## 1. ECR repository

```bash
aws ecr create-repository --repository-name handbook-app \
  --image-scanning-configuration scanOnPush=true

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/handbook-app"

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com"

docker build -t handbook-app:latest .
docker tag handbook-app:latest "${ECR_URI}:latest"
docker push "${ECR_URI}:latest"
```

Minimal `Dockerfile`:

```dockerfile
FROM nginx:1.27-alpine
COPY index.html /usr/share/nginx/html/index.html
```

---

## 2. ECS cluster & task definition

```bash
aws ecs create-cluster --cluster-name handbook-cluster

# task-def.json — Fargate, awsvpc networking
aws ecs register-task-definition --cli-input-json file://task-def.json
```

Key fields: `requiresCompatibilities: ["FARGATE"]`, `networkMode: awsvpc`, CPU/memory, execution role (`AmazonECSTaskExecutionRolePolicy`).

---

## 3. Run task & service

```bash
aws ecs run-task \
  --cluster handbook-cluster \
  --task-definition handbook-app:1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_PUB1],securityGroups=[$SG_ID],assignPublicIp=ENABLED}"

aws ecs create-service \
  --cluster handbook-cluster \
  --service-name handbook-svc \
  --task-definition handbook-app:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --load-balancers targetGroupArn="$TG_ARN",containerName=app,containerPort=80 \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_PUB1,$SUBNET_PUB2],securityGroups=[$SG_ID],assignPublicIp=ENABLED}"
```

---

## 4. Operations

```bash
aws ecs list-tasks --cluster handbook-cluster --service-name handbook-svc
aws ecs describe-tasks --cluster handbook-cluster --tasks TASK_ARN
aws ecs update-service --cluster handbook-cluster --service-name handbook-svc --force-new-deployment
```

---

## 5. Lab — Day 21

1. Build/push nginx image to ECR.
2. Fargate service ×2 behind existing ALB target group.
3. Rolling deploy new image tag; watch deployments.
4. Scale to 0; delete service, cluster, ECR images, repo.

**Previous:** [Day 20](../day20/) · **Next:** [Day 22 — Secrets & SSM](../day22/)
