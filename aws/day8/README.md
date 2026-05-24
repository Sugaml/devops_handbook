# Day 8 — VPC: Subnets, Route Tables & Internet Gateway

**Goal:** Build a custom VPC with public subnets, internet gateway, and routing from scratch via CLI.

**Time:** 5–6 hours

**Services:** VPC, EC2

---

## 1. Create VPC

```bash
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=handbook-vpc}]' \
  --query 'Vpc.VpcId' --output text)

aws ec2 modify-vpc-attribute --vpc-id "$VPC_ID" --enable-dns-hostnames
aws ec2 modify-vpc-attribute --vpc-id "$VPC_ID" --enable-dns-support
```

---

## 2. Subnets across AZs

```bash
AZ1=$(aws ec2 describe-availability-zones --query 'AvailabilityZones[0].ZoneName' --output text)
AZ2=$(aws ec2 describe-availability-zones --query 'AvailabilityZones[1].ZoneName' --output text)

SUBNET_PUB1=$(aws ec2 create-subnet --vpc-id "$VPC_ID" --cidr-block 10.0.1.0/24 \
  --availability-zone "$AZ1" \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=handbook-public-1}]' \
  --query 'Subnet.SubnetId' --output text)

SUBNET_PUB2=$(aws ec2 create-subnet --vpc-id "$VPC_ID" --cidr-block 10.0.2.0/24 \
  --availability-zone "$AZ2" \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=handbook-public-2}]' \
  --query 'Subnet.SubnetId' --output text)

aws ec2 modify-subnet-attribute --subnet-id "$SUBNET_PUB1" --map-public-ip-on-launch
```

---

## 3. Internet gateway

```bash
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=handbook-igw}]' \
  --query 'InternetGateway.InternetGatewayId' --output text)
aws ec2 attach-internet-gateway --internet-gateway-id "$IGW_ID" --vpc-id "$VPC_ID"
```

---

## 4. Route tables

```bash
RT_PUBLIC=$(aws ec2 create-route-table --vpc-id "$VPC_ID" \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=handbook-public-rt}]' \
  --query 'RouteTable.RouteTableId' --output text)

aws ec2 create-route --route-table-id "$RT_PUBLIC" \
  --destination-cidr-block 0.0.0.0/0 --gateway-id "$IGW_ID"

aws ec2 associate-route-table --route-table-id "$RT_PUBLIC" --subnet-id "$SUBNET_PUB1"
aws ec2 associate-route-table --route-table-id "$RT_PUBLIC" --subnet-id "$SUBNET_PUB2"

aws ec2 describe-route-tables --filters Name=vpc-id,Values="$VPC_ID" --output table
```

---

## 5. Launch in custom VPC

```bash
aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type t3.micro \
  --subnet-id "$SUBNET_PUB1" \
  --security-group-ids "$SG_ID" \
  --associate-public-ip-address \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=handbook-vpc-web}]'
```

**DevOps note:** Production uses **private subnets** for apps; public only for ALB or bastion.

---

## 6. Lab — Day 8

1. Create VPC `10.0.0.0/16` with two public subnets in different AZs.
2. Attach IGW; verify `0.0.0.0/0` route.
3. Launch instance; confirm public IP and internet (`curl https://aws.amazon.com`).
4. Draw diagram (paper or mermaid) of VPC components.
5. **Teardown:** terminate instances, delete subnets, detach/delete IGW, delete VPC.

**Previous:** [Day 7](../day7/) · **Next:** [Day 9 — NAT & endpoints](../day9/)
