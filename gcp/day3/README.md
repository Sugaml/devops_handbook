# Day 3 — Compute Engine: VMs, Disks & SSH

**Goal:** Launch and manage Compute Engine virtual machines, attach persistent disks, connect via SSH, and use metadata/startup scripts like a DevOps engineer.

**Time:** 4–6 hours

**Services:** Compute Engine, OS Login (intro)

---

## 1. Compute Engine model

| Concept | Description |
|---------|-------------|
| **Machine type** | vCPU + memory (`e2-micro`, `n2-standard-4`) |
| **Image** | Boot disk source (`debian-12`, `ubuntu-2404-lts`) |
| **Persistent disk** | Network block storage ( survives VM delete if retained) |
| **Preemptible / Spot** | Cheap, can be terminated with 30s notice |
| **Metadata** | Key/value on VM — SSH keys, startup scripts |

```bash
export GCP_PROJECT="${GCP_PROJECT:-devops-handbook-lab}"
export GCP_ZONE="${GCP_ZONE:-us-central1-a}"
export GCP_REGION="${GCP_REGION:-us-central1}"
```

---

## 2. List images and machine types

```bash
# Recent Debian images
gcloud compute images list --filter="family:debian-12" \
  --format="table(name,family,status)" --limit=5

# Machine types in zone
gcloud compute machine-types list --zones="$GCP_ZONE" \
  --filter="name:e2*" --format="table(name,guestCpus,memoryMb)" | head -10
```

**DevOps note:** Pin image family in Terraform/IaC (`family=debian-12`) so patches roll forward; pin image name only when you need immutability.

---

## 3. Create a VM

```bash
export VM_NAME="handbook-web-01"

gcloud compute instances create "$VM_NAME" \
  --zone="$GCP_ZONE" \
  --machine-type=e2-micro \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --boot-disk-size=10GB \
  --boot-disk-type=pd-balanced \
  --tags=http-server \
  --labels=env=lab,role=web \
  --metadata=startup-script='#!/bin/bash
apt-get update -y
apt-get install -y nginx
systemctl enable nginx
systemctl start nginx
echo "Handbook Day 3" > /var/www/html/index.html
'

# Wait until RUNNING
gcloud compute instances describe "$VM_NAME" --zone="$GCP_ZONE" \
  --format="get(status)"
```

List and filter:

```bash
gcloud compute instances list --format="table(name,zone,machineType,status,networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP)"
```

---

## 4. SSH access

### gcloud-managed SSH (simplest for labs)

```bash
gcloud compute ssh "$VM_NAME" --zone="$GCP_ZONE"
# Creates ephemeral key in ~/.ssh/google_compute_engine

# Run remote command
gcloud compute ssh "$VM_NAME" --zone="$GCP_ZONE" --command="curl -s localhost"
```

### Metadata SSH keys (legacy pattern)

```bash
# Add your public key to project metadata (all VMs inherit — broad)
gcloud compute project-info add-metadata \
  --metadata ssh-keys="handbook:$(cat ~/.ssh/id_ed25519.pub)"

ssh -i ~/.ssh/id_ed25519 USER@EXTERNAL_IP
```

**Production:** enable **OS Login** — IAM controls SSH, audit trail in Cloud Logging.

```bash
gcloud compute project-info add-metadata --metadata enable-oslogin=TRUE
# Grant roles/compute.osLogin or compute.osAdminLogin
```

---

## 5. Stop, start, reset

```bash
gcloud compute instances stop "$VM_NAME" --zone="$GCP_ZONE"
# CPU charges stop; disk + static IP may still bill

gcloud compute instances start "$VM_NAME" --zone="$GCP_ZONE"

gcloud compute instances reset "$VM_NAME" --zone="$GCP_ZONE"   # hard reboot
```

---

## 6. Persistent disks

```bash
export DATA_DISK="handbook-data-01"

# Create standalone disk
gcloud compute disks create "$DATA_DISK" \
  --zone="$GCP_ZONE" \
  --size=20GB \
  --type=pd-balanced \
  --labels=env=lab

# Attach to running VM
gcloud compute instances attach-disk "$VM_NAME" \
  --zone="$GCP_ZONE" \
  --disk="$DATA_DISK" \
  --device-name=data

# On VM (via SSH): format once, mount
# sudo mkfs.ext4 -F /dev/disk/by-id/google-data
# sudo mkdir -p /mnt/data && sudo mount /dev/disk/by-id/google-data /mnt/data
```

Detach and snapshot:

```bash
gcloud compute instances detach-disk "$VM_NAME" \
  --zone="$GCP_ZONE" --disk="$DATA_DISK"

gcloud compute disks snapshot "$DATA_DISK" \
  --zone="$GCP_ZONE" \
  --snapshot-names="${DATA_DISK}-snap-$(date +%Y%m%d)"
```

---

## 7. Instance templates & MIG preview

Managed Instance Groups (MIG) use templates — Week 2 topic; create a template now for familiarity:

```bash
gcloud compute instance-templates create handbook-web-tmpl \
  --machine-type=e2-micro \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --tags=http-server \
  --metadata=startup-script='#!/bin/bash
apt-get update && apt-get install -y nginx'
```

Templates are immutable; new versions get new names or you create a new template resource.

---

## 8. Spot VMs (cost optimization)

```bash
gcloud compute instances create handbook-spot \
  --zone="$GCP_ZONE" \
  --machine-type=e2-small \
  --provisioning-model=SPOT \
  --instance-termination-action=STOP \
  --image-family=debian-12 \
  --image-project=debian-cloud
```

Use for batch jobs, CI workers, fault-tolerant workloads — not single-node databases.

---

## 9. Serial console & troubleshooting

```bash
# View serial port output (boot errors)
gcloud compute instances get-serial-port-output "$VM_NAME" --zone="$GCP_ZONE" | tail -30

# Instance metadata
gcloud compute instances describe "$VM_NAME" --zone="$GCP_ZONE" \
  --format="yaml(metadata.items)"
```

---

## 10. Lab — Day 3

1. Create `handbook-web-01` with startup script installing nginx.
2. SSH in; verify `curl localhost` returns your HTML.
3. Create and attach a 20 GB data disk; format and mount at `/mnt/data`.
4. Stop the VM, start it, confirm disk mount persists (add `/etc/fstab` entry).
5. Snapshot the data disk.
6. Optional: create one Spot VM and observe pricing in console.

**Teardown:**

```bash
gcloud compute instances delete handbook-spot --zone="$GCP_ZONE" --quiet 2>/dev/null || true
gcloud compute instances delete "$VM_NAME" --zone="$GCP_ZONE" --quiet
gcloud compute disks delete "$DATA_DISK" --zone="$GCP_ZONE" --quiet
gcloud compute snapshots list --filter="name~handbook-data" --format="value(name)" \
  | xargs -r gcloud compute snapshots delete --quiet
gcloud compute instance-templates delete handbook-web-tmpl --quiet 2>/dev/null || true
```

**Success criteria:** VM reachable via `gcloud compute ssh`; nginx serves content; you can attach/detach disks.

---

## 11. Key takeaways

- VMs are **zonal** — disk and VM must share zone.
- **Startup scripts** bootstrap config; golden images + MIGs scale this pattern.
- **Stop** vs **delete** — delete releases most charges; disks can outlive VMs.
- Prefer **OS Login** and **Spot** where appropriate in production.

**Previous:** [Day 2 — IAM & service accounts](../day2/) · **Next:** [Day 4 — VPC & firewall rules](../day4/)
