# Day 9 — NAT Gateway, Private Subnets & VPC Endpoints

**Goal:** Add private subnets with NAT for outbound internet, and S3 gateway endpoints to reduce cost and exposure.

**Time:** 5–6 hours (includes NAT cost warning)

**Services:** VPC, EC2

---

## 1. Private subnet + NAT

```bash
SUBNET_PRIV1=$(aws ec2 create-subnet --vpc-id "$VPC_ID" --cidr-block 10.0.10.0/24 \
  --availability-zone "$AZ1" \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=handbook-private-1}]' \
  --query 'Subnet.SubnetId' --output text)

# Elastic IP for NAT
EIP_NAT=$(aws ec2 allocate-address --domain vpc --query AllocationId --output text)
NAT_GW=$(aws ec2 create-nat-gateway --subnet-id "$SUBNET_PUB1" \
  --allocation-id "$EIP_NAT" \
  --query 'NatGateway.NatGatewayId' --output text)
aws ec2 wait nat-gateway-available --nat-gateway-ids "$NAT_GW"

RT_PRIVATE=$(aws ec2 create-route-table --vpc-id "$VPC_ID" \
  --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id "$RT_PRIVATE" \
  --destination-cidr-block 0.0.0.0/0 --nat-gateway-id "$NAT_GW"
aws ec2 associate-route-table --route-table-id "$RT_PRIVATE" --subnet-id "$SUBNET_PRIV1"
```

---

## 2. NACL (optional hardening)

```bash
aws ec2 describe-network-acls --filters Name=vpc-id,Values="$VPC_ID"
# Default allows all; customize for compliance subnets
```

---

## 3. S3 gateway endpoint

```bash
aws ec2 create-vpc-endpoint --vpc-id "$VPC_ID" \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids "$RT_PRIVATE" "$RT_PUBLIC"
```

---

## 4. Interface endpoint (SSM example)

```bash
aws ec2 create-vpc-endpoint --vpc-id "$VPC_ID" \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.us-east-1.ssm \
  --subnet-ids "$SUBNET_PRIV1" \
  --security-group-ids "$SG_ID"
```

**Cost:** Interface endpoints bill hourly per AZ; gateway endpoints for S3/DynamoDB are free.

---

## 5. Lab — Day 9

1. Extend Day 8 VPC with private subnet and NAT.
2. Launch instance in private subnet **without** public IP; use SSM Session Manager (Day 25) or bastion for access.
3. From private instance: `curl https://example.com` (via NAT).
4. Add S3 gateway endpoint; verify S3 access without NAT path for S3 traffic.
5. **Teardown:** delete NAT gateway first (stops main charge), release EIP, then subnets/VPC.

**Previous:** [Day 8](../day8/) · **Next:** [Day 10 — Load balancers](../day10/)
