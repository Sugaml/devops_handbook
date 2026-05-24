# Day 4 — Virtual Networks, Subnets, NSGs & Public IPs

**Goal:** Design and deploy a production-style VNet; control traffic with NSGs, understand default routes, and expose services safely with public IPs and DNS.

**Time:** 4–6 hours

**Services:** Virtual Network, NSG, Public IP, DNS (intro)

---

## 1. VNet design vocabulary

| Component | Purpose |
|-----------|---------|
| **VNet** | Private IPv4/IPv6 network boundary in a region |
| **Subnet** | Segment within VNet — resources get IPs from subnet range |
| **NSG** | Stateful L4 firewall rules (allow/deny) |
| **Route table** | Custom routing (UDRs) — default routes to Internet |
| **Public IP** | Internet-facing IPv4/IPv6 address |
| **Private DNS zone** | Name resolution inside VNet (`*.internal.contoso`) |

**CIDR planning example** (single region lab):

```
VNet:     10.20.0.0/16
  subnet-web:     10.20.1.0/24
  subnet-app:     10.20.2.0/24
  subnet-data:    10.20.3.0/24   (often no direct internet)
```

**DevOps rule:** Never overlap VNet address spaces you might peer or connect via VPN/ExpressRoute.

---

## 2. Create VNet and subnets

```bash
export LAB_RG=rg-devops-handbook
export LAB_LOCATION=eastus
export VNET_NAME=vnet-handbook
export SUBNET_WEB=subnet-web

az network vnet create \
  --resource-group $LAB_RG \
  --location $LAB_LOCATION \
  --name $VNET_NAME \
  --address-prefix 10.20.0.0/16 \
  --subnet-name $SUBNET_WEB \
  --subnet-prefix 10.20.1.0/24 \
  --tags Project=devops-handbook Day=4

# Additional subnets
az network vnet subnet create \
  --resource-group $LAB_RG \
  --vnet-name $VNET_NAME \
  --name subnet-app \
  --address-prefix 10.20.2.0/24

az network vnet subnet create \
  --resource-group $LAB_RG \
  --vnet-name $VNET_NAME \
  --name subnet-data \
  --address-prefix 10.20.3.0/24

az network vnet show --resource-group $LAB_RG --name $VNET_NAME \
  --query "{Name:name, Prefix:addressSpace.addressPrefixes, Subnets:subnets[].name}" -o jsonc
```

---

## 3. Network Security Groups (NSGs)

NSG rules have **priority** (100–4096, lower = evaluated first), direction, ports, and prefixes.

### Create NSG and rules

```bash
export NSG_NAME=nsg-web

az network nsg create \
  --resource-group $LAB_RG \
  --location $LAB_LOCATION \
  --name $NSG_NAME \
  --tags Project=devops-handbook

# Allow SSH from your IP only (replace with your public IP)
MY_IP=$(curl -s ifconfig.me)
az network nsg rule create \
  --resource-group $LAB_RG \
  --nsg-name $NSG_NAME \
  --name Allow-SSH-MyIP \
  --priority 100 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefixes "$MY_IP/32" \
  --source-port-ranges '*' \
  --destination-address-prefixes '*' \
  --destination-port-ranges 22

# Allow HTTP from Internet (lab only)
az network nsg rule create \
  --resource-group $LAB_RG \
  --nsg-name $NSG_NAME \
  --name Allow-HTTP \
  --priority 110 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefixes Internet \
  --destination-port-ranges 80

az network nsg rule list --resource-group $LAB_RG --nsg-name $NSG_NAME \
  --query "[].{Name:name, Priority:priority, Access:access, Port:destinationPortRange, Source:sourceAddressPrefix}" -o table
```

### Associate NSG with subnet

```bash
az network vnet subnet update \
  --resource-group $LAB_RG \
  --vnet-name $VNET_NAME \
  --name $SUBNET_WEB \
  --network-security-group $NSG_NAME
```

**Default NSG rules** still allow VNet inbound and Azure Load Balancer probes — review in portal or:

```bash
az network nsg show --resource-group $LAB_RG --name $NSG_NAME \
  --query "defaultSecurityRules[].{Name:name, Access:access, Direction:direction}" -o table
```

---

## 4. VM in custom VNet

If you kept `vm-handbook-day3` from quick-create, it lives in a default VNet. Create a new VM in your designed subnet:

```bash
export VM_NAME=vm-handbook-net
export ADMIN_USER=azureuser
export AZURE_VM_SSH_KEY=~/.ssh/azure_handbook_ed25519.pub

az vm create \
  --resource-group $LAB_RG \
  --name $VM_NAME \
  --location $LAB_LOCATION \
  --image Ubuntu2204 \
  --size Standard_B1s \
  --admin-username $ADMIN_USER \
  --authentication-type ssh \
  --ssh-key-values @$AZURE_VM_SSH_KEY \
  --vnet-name $VNET_NAME \
  --subnet $SUBNET_WEB \
  --nsg $NSG_NAME \
  --public-ip-sku Standard \
  --assign-identity \
  --tags Project=devops-handbook Day=4

VM_IP=$(az vm show -d -g $LAB_RG -n $VM_NAME --query publicIps -o tsv)

# Install nginx for connectivity test
az vm run-command invoke -g $LAB_RG -n $VM_NAME \
  --command-id RunShellScript \
  --scripts "sudo apt-get update && sudo apt-get install -y nginx && echo net-day4 > /var/www/html/index.html"

curl -s --max-time 5 "http://$VM_IP/" || echo "Check NSG and public IP"
```

---

## 5. Public IP resources

```bash
# List public IPs
az network public-ip list --resource-group $LAB_RG \
  --query "[].{Name:name, IP:ipAddress, SKU:sku.name, Allocation:publicIpAllocationMethod}" -o table

# Create static Standard SKU IP (for load balancers, AKS ingress)
az network public-ip create \
  --resource-group $LAB_RG \
  --name pip-handbook-lb \
  --sku Standard \
  --allocation-method Static \
  --tags Project=devops-handbook

az network public-ip show --resource-group $LAB_RG --name pip-handbook-lb \
  --query ipAddress -o tsv
```

| SKU | Use |
|-----|-----|
| Basic | Legacy — avoid for new designs |
| Standard | Zone-redundant option; required for Standard LB |

---

## 6. Effective security rules (debugging)

When traffic fails, check **effective** rules on the NIC:

```bash
NIC_ID=$(az vm show -g $LAB_RG -n $VM_NAME --query "networkProfile.networkInterfaces[0].id" -o tsv)
NIC_NAME=$(basename $NIC_ID)

az network nic list-effective-nsg --resource-group $LAB_RG --name $NIC_NAME -o table
```

Common failures:

| Symptom | Check |
|---------|-------|
| SSH timeout | NSG source IP, public IP attached, VM running |
| Connection refused | App listening (`ss -tlnp`), not NSG |
| Works from VNet but not Internet | Missing public IP or LB front-end |

---

## 7. Private DNS (optional lab)

```bash
az network private-dns zone create \
  --resource-group $LAB_RG \
  --name handbook.internal

az network private-dns link vnet create \
  --resource-group $LAB_RG \
  --zone-name handbook.internal \
  --name link-vnet-handbook \
  --virtual-network $VNET_NAME \
  --registration-enabled false

az network private-dns record-set a add-record \
  --resource-group $LAB_RG \
  --zone-name handbook.internal \
  --record-set-name web \
  --ipv4-address 10.20.1.4   # private IP of VM — get from az vm show -d
```

Test from inside VNet (SSH to VM):

```bash
dig web.handbook.internal +short
```

---

## 8. VNet peering (concept)

Peering connects two VNets (same or different region) with low latency.

```bash
# Second VNet in same region (lab sketch)
az network vnet create -g $LAB_RG -n vnet-handbook-b \
  --address-prefix 10.30.0.0/16 --subnet-name default --subnet-prefix 10.30.1.0/24

az network vnet peering create \
  --resource-group $LAB_RG \
  --name peer-a-to-b \
  --vnet-name $VNET_NAME \
  --remote-vnet vnet-handbook-b \
  --allow-vnet-access

az network vnet peering create \
  --resource-group $LAB_RG \
  --name peer-b-to-a \
  --vnet-name vnet-handbook-b \
  --remote-vnet $VNET_NAME \
  --allow-vnet-access
```

Peering is **non-transitive** — hub-spoke topologies need a hub NVA or mesh design.

---

## 9. Lab — Day 4

1. Create `vnet-handbook` `10.20.0.0/16` with subnets `subnet-web`, `subnet-app`, `subnet-data`.
2. Create `nsg-web` with SSH allowed **only from your public IP** and HTTP from Internet.
3. Deploy `vm-handbook-net` into `subnet-web` with that NSG.
4. Install nginx; verify `curl http://PUBLIC_IP/`.
5. Run `az network nic list-effective-nsg` and screenshot or save output.
6. **Optional:** Add private DNS zone and A record; resolve from VM.

**Success criteria:** HTTP works from your laptop; SSH blocked if you remove your IP rule (test carefully).

---

## 10. Teardown

```bash
az vm delete -g $LAB_RG -n vm-handbook-net --yes --no-wait
az vm delete -g $LAB_RG -n vm-handbook-day3 --yes --no-wait 2>/dev/null || true

# Delete peering partner if created
az network vnet delete -g $LAB_RG -n vnet-handbook-b --yes 2>/dev/null || true

az network public-ip delete -g $LAB_RG -n pip-handbook-lb --yes 2>/dev/null || true
# Keep VNet for Day 7 or delete entire RG at end of week
```

---

## 11. Key takeaways

- **NSG + public IP + app listening** — all three must align for inbound traffic.
- Restrict SSH to known IPs; use **Azure Bastion** or **VPN** in production instead of wide-open port 22.
- Use `list-effective-nsg` when rules look correct but traffic still fails.

**Previous:** [Day 3](../day3/) · **Next:** [Day 5 — Storage & Bicep basics](../day5/)
