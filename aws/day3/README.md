# Day 3 — EC2: Instances, AMIs & Key Pairs

**Goal:** Launch, connect to, and manage EC2 instances; work with AMIs and instance types from the CLI.

**Time:** 4–6 hours

**Services:** EC2

---

## 1. Discover images and types

```bash
# Latest Amazon Linux 2023 AMI (SSM parameter — preferred)
aws ssm get-parameters \
  --names /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --query 'Parameters[0].Value' --output text

# Or search owned by Amazon
aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=al2023-ami-*-x86_64" "Name=state,Values=available" \
  --query 'sort_by(Images,&CreationDate)[-1].[ImageId,Name]' --output text

# Instance types (filter by vCPU)
aws ec2 describe-instance-types \
  --filters Name=vcpu-info.default-vcpus,Values=2 \
  --query 'InstanceTypes[?starts_with(InstanceType,`t`)].InstanceType' \
  --output table | head -20
```

| Family | Use case |
|--------|----------|
| `t3` / `t4g` | Burstable dev/test |
| `m7i` / `m7g` | General purpose |
| `c7i` | Compute optimized |
| `r7i` | Memory optimized |

---

## 2. Key pairs

```bash
aws ec2 create-key-pair --key-name handbook-key \
  --query 'KeyMaterial' --output text > ~/.ssh/handbook-key.pem
chmod 400 ~/.ssh/handbook-key.pem

aws ec2 describe-key-pairs --key-names handbook-key
aws ec2 delete-key-pair --key-name handbook-key
```

---

## 3. Security group (minimal)

```bash
VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true \
  --query 'Vpcs[0].VpcId' --output text)

aws ec2 create-security-group \
  --group-name handbook-sg \
  --description "SSH from my IP" \
  --vpc-id "$VPC_ID"

MY_IP=$(curl -s https://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress \
  --group-name handbook-sg \
  --protocol tcp --port 22 --cidr "${MY_IP}/32"
```

---

## 4. Launch instance

```bash
AMI_ID=$(aws ssm get-parameters \
  --names /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --query 'Parameters[0].Value' --output text)

INSTANCE_ID=$(aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type t3.micro \
  --key-name handbook-key \
  --security-groups handbook-sg \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=handbook-day3},{Key=Project,Value=devops-handbook}]" \
  --query 'Instances[0].InstanceId' --output text)

echo "Instance: $INSTANCE_ID"
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"
aws ec2 describe-instances --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].{State:State.Name,IP:PublicIpAddress,AZ:Placement.AvailabilityZone}'
```

---

## 5. Connect and manage

```bash
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

ssh -i ~/.ssh/handbook-key.pem ec2-user@"$PUBLIC_IP"

# From another terminal — instance state
aws ec2 describe-instance-status --instance-ids "$INSTANCE_ID"
aws ec2 stop-instances --instance-ids "$INSTANCE_ID"
aws ec2 wait instance-stopped --instance-ids "$INSTANCE_ID"
aws ec2 start-instances --instance-ids "$INSTANCE_ID"
aws ec2 reboot-instances --instance-ids "$INSTANCE_ID"
```

---

## 6. User data (bootstrap)

`userdata.sh`:

```bash
#!/bin/bash
dnf install -y nginx
systemctl enable --now nginx
echo "handbook-day3" > /usr/share/nginx/html/index.html
```

```bash
aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type t3.micro \
  --security-groups handbook-sg \
  --user-data file://userdata.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=handbook-web}]' \
  --query 'Instances[0].InstanceId' --output text
```

---

## 7. AMIs and cleanup

```bash
# Create AMI from running instance (brief downtime if no reboot opt)
aws ec2 create-image \
  --instance-id "$INSTANCE_ID" \
  --name "handbook-ami-$(date +%Y%m%d)" \
  --no-reboot

aws ec2 describe-images --owners self --query 'Images[].Name' --output table

# Terminate (stops billing for instance; EBS root may persist per settings)
aws ec2 terminate-instances --instance-ids "$INSTANCE_ID"
aws ec2 wait instance-terminated --instance-ids "$INSTANCE_ID"
```

**DevOps note:** Golden AMIs are largely replaced by **launch templates + cloud-init** or container images—but AMIs remain common for licensed software.

---

## 8. Lab — Day 3

1. Create key pair; launch `t3.micro` with Name tag.
2. SSH in; install `htop`, verify identity with `aws sts get-caller-identity` (will fail without instance role—that is expected).
3. Launch second instance with user data nginx; curl public IP.
4. Stop one instance; start it; confirm new public IP (unless Elastic IP—Day 4).
5. Terminate all lab instances; delete security group if unused.

**Previous:** [Day 2](../day2/) · **Next:** [Day 4 — Security groups & networking](../day4/)
