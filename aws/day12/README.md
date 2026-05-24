# Day 12 — EBS Volumes, Snapshots & AMIs

**Goal:** Attach and resize EBS volumes, take snapshots, copy across regions, and bake AMIs.

**Time:** 4–5 hours

**Services:** EBS, EC2

---

## 1. Create and attach volume

```bash
AZ=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].Placement.AvailabilityZone' --output text)

VOL_ID=$(aws ec2 create-volume --availability-zone "$AZ" \
  --size 10 --volume-type gp3 --iops 3000 --throughput 125 \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=handbook-data}]' \
  --query 'VolumeId' --output text)
aws ec2 wait volume-available --volume-ids "$VOL_ID"

aws ec2 attach-volume --volume-id "$VOL_ID" --instance-id "$INSTANCE_ID" --device /dev/xvdf
# On instance: mkfs, mount (ext4/xfs)
```

---

## 2. Snapshots

```bash
SNAP_ID=$(aws ec2 create-snapshot --volume-id "$VOL_ID" \
  --description "handbook day12" --query SnapshotId --output text)
aws ec2 wait snapshot-completed --snapshot-ids "$SNAP_ID"

aws ec2 describe-snapshots --owner-ids self --output table
```

---

## 3. Copy snapshot (DR)

```bash
aws ec2 copy-snapshot --source-region us-east-1 --source-snapshot-id "$SNAP_ID" \
  --destination-region us-west-2 --description "DR copy"
```

---

## 4. Volume from snapshot

```bash
aws ec2 create-volume --snapshot-id "$SNAP_ID" --availability-zone "$AZ"
```

---

## 5. Lab — Day 12

1. Attach 10 GB gp3 volume; format and mount at `/data`.
2. Write test files; snapshot volume.
3. Detach volume; create new volume from snapshot; attach to second instance; verify data.
4. Delete snapshots and volumes; document gp3 vs gp2 cost note.

**Previous:** [Day 11](../day11/) · **Next:** [Day 13 — Route 53](../day13/)
