# Day 3 — Resource Groups, Virtual Machines, Disks & SSH

**Goal:** Deploy and operate Linux VMs from the CLI; understand SKUs, NICs, OS disks, cloud-init, and managed identity on compute.

**Time:** 4–6 hours

**Services:** Compute, Network (NIC), Managed Disks

---

## 1. Compute concepts

| Concept | Description |
|---------|-------------|
| **VM size (SKU)** | vCPU, RAM, temp storage — e.g. `Standard_B1s` |
| **Image** | OS template — `Ubuntu2204`, `Debian12`, RHEL |
| **OS disk** | Persistent boot disk (Premium SSD, Standard SSD, Standard HDD) |
| **Data disk** | Optional additional volumes |
| **NIC** | Network interface — IP config, NSG association |
| **Cloud-init** | First-boot customization (users, packages, scripts) |

**DevOps note:** Prefer **Infrastructure as Code** (Bicep Day 5/7) over hand-typed `az vm create` in production — CLI here teaches the underlying resources.

---

## 2. SSH key pair (do this first)

```bash
# Generate if you do not have one
ssh-keygen -t ed25519 -C "devops-handbook" -f ~/.ssh/azure_handbook_ed25519 -N ""

# Azure CLI accepts public key path
export AZURE_VM_SSH_KEY=~/.ssh/azure_handbook_ed25519.pub
cat $AZURE_VM_SSH_KEY
```

Never paste private keys into tickets, chat, or repos.

---

## 3. Create a VM (all-in-one)

```bash
export LAB_RG=rg-devops-handbook
export LAB_LOCATION=eastus
export VM_NAME=vm-handbook-day3
export ADMIN_USER=azureuser

az vm create \
  --resource-group $LAB_RG \
  --location $LAB_LOCATION \
  --name $VM_NAME \
  --image Ubuntu2204 \
  --size Standard_B1s \
  --admin-username $ADMIN_USER \
  --authentication-type ssh \
  --ssh-key-values @$AZURE_VM_SSH_KEY \
  --public-ip-sku Standard \
  --assign-identity \
  --tags Project=devops-handbook Day=3 \
  --output table
```

What Azure creates behind one command:

- Virtual network + subnet (default)
- Network security group + rules (SSH allowed by default on quick create)
- Public IP
- NIC
- OS disk
- VM with **system-assigned managed identity**

---

## 4. Connect and verify

```bash
# Get public IP
VM_IP=$(az vm show -d --resource-group $LAB_RG --name $VM_NAME \
  --query publicIps -o tsv)
echo "ssh $ADMIN_USER@$VM_IP"

ssh -i ~/.ssh/azure_handbook_ed25519 -o StrictHostKeyChecking=accept-new \
  $ADMIN_USER@$VM_IP

# On the VM
uname -a
curl -s -H Metadata:true \
  "http://169.254.169.254/metadata/instance?api-version=2021-02-01" | jq .compute
exit
```

### Instance metadata (IMDS)

```bash
# Useful fields from inside VM
curl -s -H Metadata:true \
  "http://169.254.169.254/metadata/instance/compute?api-version=2021-02-01&format=json" | jq .
```

Use IMDS for region-aware scripts — not hard-coded region names in app config.

---

## 5. VM operations

```bash
# Power state
az vm get-instance-view --resource-group $LAB_RG --name $VM_NAME \
  --query "instanceView.statuses[?starts_with(code, 'PowerState/')].displayStatus" -o tsv

# Stop (deallocate — stops billing compute; disk/IP may still cost)
az vm deallocate --resource-group $LAB_RG --name $VM_NAME

# Start
az vm start --resource-group $LAB_RG --name $VM_NAME

# Restart
az vm restart --resource-group $LAB_RG --name $VM_NAME

# Resize (must deallocate for some SKUs)
az vm deallocate -g $LAB_RG -n $VM_NAME
az vm resize -g $LAB_RG -n $VM_NAME --size Standard_B2s
az vm start -g $LAB_RG -n $VM_NAME

# List VMs in RG
az vm list --resource-group $LAB_RG \
  --query "[].{Name:name, Size:hardwareProfile.vmSize, Provisioning:provisioningState}" -o table
```

---

## 6. Disks

```bash
# List disks attached to VM
az vm show --resource-group $LAB_RG --name $VM_NAME \
  --query "storageProfile.{OS:osDisk.name, Data:dataDisks[].name}" -o jsonc

# Create empty data disk
az disk create \
  --resource-group $LAB_RG \
  --name disk-handbook-data01 \
  --size-gb 32 \
  --sku StandardSSD_LRS \
  --tags Project=devops-handbook

# Attach to VM
az vm disk attach \
  --resource-group $LAB_RG \
  --vm-name $VM_NAME \
  --name disk-handbook-data01 \
  --new

# On VM — partition, format, mount (ext4 example)
# lsblk
# sudo mkfs.ext4 /dev/sdc
# sudo mkdir /data && echo '/dev/sdc /data ext4 defaults,nofail 0 2' | sudo tee -a /etc/fstab
# sudo mount -a
```

Snapshot (backup primitive):

```bash
OS_DISK_ID=$(az vm show -g $LAB_RG -n $VM_NAME --query "storageProfile.osDisk.managedDisk.id" -o tsv)

az snapshot create \
  --resource-group $LAB_RG \
  --name snap-osdisk-day3 \
  --source "$OS_DISK_ID"
```

Use resource ID from `az disk list -g $LAB_RG -o table` if the above shortcut fails.

---

## 7. Cloud-init / custom data

Create `cloud-init.yaml`:

```yaml
#cloud-config
package_update: true
packages:
  - nginx
  - jq
runcmd:
  - systemctl enable nginx
  - systemctl start nginx
  - echo "handbook-day3" > /var/www/html/index.html
```

Deploy **new** VM with custom data (or use for next lab iteration):

```bash
az vm create \
  --resource-group $LAB_RG \
  --name vm-handbook-cloudinit \
  --image Ubuntu2204 \
  --size Standard_B1s \
  --admin-username $ADMIN_USER \
  --authentication-type ssh \
  --ssh-key-values @$AZURE_VM_SSH_KEY \
  --custom-data cloud-init.yaml \
  --public-ip-sku Standard \
  --tags Project=devops-handbook
```

Debug cloud-init on VM:

```bash
ssh -i ~/.ssh/azure_handbook_ed25519 $ADMIN_USER@$VM_IP \
  'sudo cloud-init status --long; sudo cat /var/log/cloud-init-output.log | tail -30'
```

---

## 8. Run command (agentless ops)

Execute scripts without SSH — useful when NSG blocks your IP but Azure control plane works:

```bash
az vm run-command invoke \
  --resource-group $LAB_RG \
  --name $VM_NAME \
  --command-id RunShellScript \
  --scripts "hostname; uptime; df -h /"

az vm run-command list --location $LAB_LOCATION -o table
```

Requires **VM Agent** installed (default on Azure gallery images).

---

## 9. Managed identity on VM (tie-in to Day 2)

```bash
# Confirm identity
az vm show --resource-group $LAB_RG --name $VM_NAME \
  --query identity -o jsonc

# Login to Azure CLI *from inside VM* using managed identity
# (install az cli on VM first, or use IMDS token directly)
az login --identity
az account show -o table
```

Grant minimal RBAC to the VM identity before relying on it in apps.

---

## 10. Lab — Day 3

1. Generate SSH key pair if needed.
2. Create `vm-handbook-day3` (`Standard_B1s`, Ubuntu 22.04) with system-assigned managed identity.
3. SSH in; fetch instance metadata; note `location` and `vmSize`.
4. Attach a 32 GB Standard SSD data disk; format and mount at `/data`.
5. Run `az vm run-command invoke` to print `df -h`.
6. **Optional:** Create second VM with cloud-init serving nginx; curl public IP on port 80.

**Success criteria:** SSH works; disk visible in `lsblk`; managed identity principal ID is non-null.

---

## 11. Teardown (partial — keep RG for Day 4)

```bash
# Delete extra cloud-init VM if created
az vm delete --resource-group $LAB_RG --name vm-handbook-cloudinit --yes --no-wait 2>/dev/null || true

# Delete snapshot and unattached disks when fully done
az snapshot delete -g $LAB_RG -n snap-osdisk-day3 --yes 2>/dev/null || true
az disk delete -g $LAB_RG -n disk-handbook-data01 --yes --no-wait 2>/dev/null || true

# Keep vm-handbook-day3 for Day 4 networking labs OR delete now:
# az vm delete -g $LAB_RG -n $VM_NAME --yes --no-wait
```

---

## 12. Key takeaways

- `az vm create` bundles network + compute — know the pieces for troubleshooting.
- **Deallocate** stops compute billing; disks and public IPs may still cost.
- **Managed identity** lets the VM authenticate to Azure APIs without secrets.

**Previous:** [Day 2](../day2/) · **Next:** [Day 4 — Virtual networks & NSGs](../day4/)
