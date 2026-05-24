# Day 1 — Azure Subscriptions, Regions & CLI Setup

**Goal:** Understand the Azure hierarchy, install Azure CLI, authenticate safely, and verify your active subscription and tenant.

**Time:** 3–5 hours

**Services:** Subscriptions, Resource Manager, Entra ID (intro)

---

## 1. Azure hierarchy (management model)

| Concept | Scope | DevOps implication |
|---------|--------|-------------------|
| **Tenant** | Entra ID directory (one org) | All RBAC identities live here |
| **Management group** | Policy & hierarchy above subscriptions | Enterprise landing zones |
| **Subscription** | Billing + quota boundary | CI/CD and envs often map 1:1 (dev/stage/prod) |
| **Resource group** | Logical container for resources | Lifecycle unit — delete RG deletes all resources |
| **Resource** | VM, storage account, VNet, etc. | Named with ARM resource ID |

**ARM resource ID format:**

```
/subscriptions/{subscription-id}/resourceGroups/{rg}/providers/{provider}/{type}/{name}
```

Example:

```
/subscriptions/aaaa-bbbb-cccc/providers/Microsoft.Compute/virtualMachines/web-01
```

**DevOps note:** Pipelines should set `AZURE_SUBSCRIPTION_ID` explicitly — never rely on whatever subscription happens to be default on an agent.

---

## 2. Regions and availability

```bash
# List regions available to your subscription
az account list-locations --query "[].{Name:name, Display:displayName}" -o table

# Pick a home region close to you — examples use eastus
export LAB_LOCATION=eastus

# Availability zones (region-specific)
az account list-locations --query "[?name=='eastus'].{Region:name, Zones:availabilityZoneMappings}" -o jsonc
```

| Term | Meaning |
|------|---------|
| Region | Geographic area (`eastus`, `westeurope`) |
| Availability Zone | Independent datacenter within region (`1`, `2`, `3`) |
| Region pair | DR pairing defined by Microsoft (not always adjacent) |

---

## 3. Install Azure CLI

```bash
# macOS (Homebrew)
brew update && brew install azure-cli

# Linux (Debian/Ubuntu)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Windows (PowerShell)
# winget install -e --id Microsoft.AzureCLI

az version
# {
#   "azure-cli": "2.x.x",
#   ...
# }
```

Upgrade:

```bash
brew upgrade azure-cli          # macOS
sudo apt update && sudo apt install azure-cli  # Debian if repo configured
```

Optional tools:

```bash
brew install jq                 # JSON parsing
az extension list-available -o table   # browse extensions
```

---

## 4. Authenticate (the right way)

**Never** run daily work as the subscription billing owner without MFA and least privilege.

| Method | Best for |
|--------|----------|
| `az login` (browser) | Humans on laptop |
| `az login --service-principal` | CI/CD (prefer federated credentials in prod — Day 7) |
| Managed identity | Workloads running **in** Azure (Day 2) |

### Interactive login

```bash
az login
# Opens browser — sign in with your work or personal Microsoft account

az account show -o table
az account list -o table --query "[].{Name:name, SubscriptionId:id, IsDefault:isDefault, State:state}"

# Set default subscription
az account set --subscription "Your Subscription Name"
# or
az account set --subscription "00000000-0000-0000-0000-000000000000"

export AZURE_SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo $AZURE_SUBSCRIPTION_ID
```

### Verify tenant and user

```bash
az account show --query "{Subscription:name, SubId:id, Tenant:tenantId, User:user.name}" -o table

az ad signed-in-user show --query "{UPN:userPrincipalName, ObjectId:id}" -o table
```

You should see your UPN (email) — **not** a generic owner account shared across a team.

---

## 5. CLI configuration & defaults

Azure CLI stores config in `~/.azure/`.

```bash
az configure list-defaults
az configure set defaults.group=rg-devops-handbook
az configure set defaults.location=eastus

# Environment variables (CI / scripts)
export AZURE_CONFIG_DIR=$HOME/.azure    # optional alternate config dir
export AZURE_DEFAULTS_GROUP=rg-devops-handbook
export AZURE_DEFAULTS_LOCATION=eastus
```

Disable interactive prompts in scripts:

```bash
export AZURE_CORE_ONLY_SHOW_ERRORS=true
export AZURE_CORE_NO_COLOR=true
```

---

## 6. First resource manager calls

```bash
# Create a resource group (idempotent with same name in same region)
az group create \
  --name rg-devops-handbook \
  --location eastus \
  --tags Project=devops-handbook Environment=lab Owner=$(whoami)

az group show --name rg-devops-handbook -o table
az group list --query "[?name=='rg-devops-handbook']" -o table

# List all resource groups
az group list --query "[].{Name:name, Location:location}" -o table

# Tag an existing RG
az group update --name rg-devops-handbook \
  --set tags.ReviewDate=$(date +%F)
```

---

## 7. CLI ergonomics

```bash
# Help for any command
az vm create -h
az find "create storage account"

# Output formats
az group list -o table
az group list -o json
az group list -o yaml

# JMESPath query (like AWS --query)
az group list --query "[?location=='eastus'].name" -o tsv

# Debug (support tickets)
az group show --name rg-devops-handbook --debug 2>&1 | tail -30

# Preview extension (upcoming CLI features)
az upgrade  # upgrade CLI itself
```

### Useful global flags

| Flag | Purpose |
|------|---------|
| `--subscription` | Override default subscription |
| `--resource-group` / `-g` | Target RG |
| `--output` / `-o` | `json`, `table`, `tsv`, `yaml` |
| `--query` | JMESPath filter |
| `--only-show-errors` | Quiet success output in scripts |

---

## 8. Cloud Shell (optional)

Azure Cloud Shell gives you a browser-based bash environment with `az`, `kubectl`, and storage preinstalled.

1. Portal → Cloud Shell icon (top bar).
2. Choose **Bash**; a storage account is created for your `$HOME` persistence.
3. Your subscription context is already authenticated.

Use Cloud Shell when you cannot install CLI locally; prefer local CLI for handbook labs so you learn config on your machine.

---

## 9. Lab — Day 1

1. Create a **Free Azure account** or use an existing subscription with Contributor access.
2. Install Azure CLI v2; run `az version`.
3. Run `az login`; set default subscription with `az account set`.
4. Record **Subscription ID** and **Tenant ID** in your notes.
5. Create resource group `rg-devops-handbook` in `eastus` with tags `Project=devops-handbook`.
6. Add shell exports to `~/.zshrc` or `~/.bashrc`:

```bash
export AZURE_SUBSCRIPTION_ID=$(az account show --query id -o tsv 2>/dev/null)
export LAB_LOCATION=eastus
export LAB_RG=rg-devops-handbook
export AZURE_DEFAULTS_GROUP=$LAB_RG
export AZURE_DEFAULTS_LOCATION=$LAB_LOCATION
```

7. Verify: `az group show -n rg-devops-handbook -o table` — no auth errors.

**Success criteria:** CLI returns your subscription; you are logged in as a named user (not a shared root-style account).

---

## 10. Key takeaways

- **Subscription** = billing + quota; **resource group** = lifecycle bucket.
- Always pin subscription and region in automation.
- `az account show` and `az ad signed-in-user show` are your "who am I?" checks.

**Next:** [Day 2 — Entra ID, RBAC & managed identity](../day2/)
