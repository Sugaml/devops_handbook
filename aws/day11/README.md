# Day 11 — Auto Scaling & Launch Templates

**Goal:** Define launch templates and Auto Scaling groups tied to ALB for elastic capacity.

**Time:** 5–6 hours

**Services:** EC2 Auto Scaling, ELBv2

---

## 1. Launch template

```bash
aws ec2 create-launch-template \
  --launch-template-name handbook-lt \
  --launch-template-data '{
    "ImageId": "'"$AMI_ID"'",
    "InstanceType": "t3.micro",
    "SecurityGroupIds": ["'"$SG_ID"'"],
    "TagSpecifications": [{
      "ResourceType": "instance",
      "Tags": [{"Key": "Project", "Value": "devops-handbook"}]
    }],
    "UserData": "'$(echo -n '#!/bin/bash
dnf install -y nginx && systemctl start nginx' | base64)'"
  }'
```

---

## 2. Auto Scaling group

```bash
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name handbook-asg \
  --launch-template LaunchTemplateName=handbook-lt,Version='$Latest' \
  --min-size 1 --max-size 3 --desired-capacity 2 \
  --vpc-zone-identifier "${SUBNET_PUB1},${SUBNET_PUB2}" \
  --target-group-arns "$TG_ARN" \
  --health-check-type ELB \
  --tags Key=Project,Value=devops-handbook,PropagateAtLaunch=true
```

---

## 3. Scaling policies

```bash
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name handbook-asg \
  --policy-name scale-out-cpu \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ASGAverageCPUUtilization"
    },
    "TargetValue": 50.0
  }'
```

---

## 4. Instance refresh & activity

```bash
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names handbook-asg
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name handbook-asg --max-items 5
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name handbook-asg --desired-capacity 3
```

---

## 5. Lab — Day 11

1. Reuse Day 10 ALB/target group.
2. Create launch template + ASG with desired=2.
3. Confirm targets healthy behind ALB.
4. Trigger scale-out (CPU stress or manual desired capacity).
5. Delete ASG (force delete instances), launch template, ALB stack.

**Previous:** [Day 10](../day10/) · **Next:** [Day 12 — EBS](../day12/)
