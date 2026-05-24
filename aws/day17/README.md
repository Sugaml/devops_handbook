# Day 17 — RDS: Relational Databases

**Goal:** Launch MySQL/PostgreSQL RDS, connect securely, snapshot, and restore.

**Time:** 5–6 hours (allow provisioning time)

**Services:** RDS, EC2 (client), Secrets Manager (optional)

---

## 1. DB subnet group (custom VPC)

```bash
aws rds create-db-subnet-group \
  --db-subnet-group-name handbook-db-subnet \
  --db-subnet-group-description "handbook" \
  --subnet-ids "$SUBNET_PRIV1" "$SUBNET_PUB2"
```

---

## 2. Security group for RDS

```bash
aws ec2 authorize-security-group-ingress \
  --group-id "$RDS_SG" --protocol tcp --port 5432 --source-group "$APP_SG"
```

---

## 3. Create instance

```bash
aws rds create-db-instance \
  --db-instance-identifier handbook-postgres \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 16.4 \
  --master-username dbadmin \
  --master-user-password 'CHANGE_ME_STRONG' \
  --allocated-storage 20 \
  --vpc-security-group-ids "$RDS_SG" \
  --db-subnet-group-name handbook-db-subnet \
  --backup-retention-period 7 \
  --no-publicly-accessible \
  --tags Key=Project,Value=devops-handbook

aws rds wait db-instance-available --db-instance-identifier handbook-postgres
aws rds describe-db-instances --db-instance-identifier handbook-postgres \
  --query 'DBInstances[0].Endpoint'
```

---

## 4. Snapshots

```bash
aws rds create-db-snapshot \
  --db-snapshot-identifier handbook-snap-$(date +%Y%m%d) \
  --db-instance-identifier handbook-postgres
aws rds wait db-snapshot-completed --db-snapshot-identifier handbook-snap-...
```

---

## 5. Lab — Day 17

1. Create Postgres `db.t3.micro` in private subnets.
2. From bastion/SSM instance, `psql` connect and create table.
3. Manual snapshot; restore to new instance identifier.
4. **Teardown:** delete instances (skip final snapshot only in throwaway lab).

**Previous:** [Day 16](../day16/) · **Next:** [Day 18 — DynamoDB](../day18/)
