# Day 7 — Bicep, Azure DevOps CI/CD & Production Patterns

**Goal:** Deploy infrastructure from a pipeline with Bicep; use Key Vault and federated identity; apply landing-zone habits — budgets, tagging, teardown runbooks.

**Time:** 5–8 hours (capstone)

**Services:** Bicep, Azure DevOps, Key Vault, Azure Policy (intro)

---

## 1. Capstone architecture

You will deploy a small **web stack** from git:

```
Git repo
  └── infra/main.bicep          → RG, VNet, NSG, VM, Storage, Key Vault
  └── infra/main.bicepparam     (or pipeline variables)
  └── .azuredevops/azure-pipelines.yml
        → validate (what-if) → deploy → smoke test
```

Production differs only in scale: private endpoints, AKS, Front Door, multiple environments — the **pipeline shape** stays the same.

---

## 2. Capstone Bicep module

Create `infra/main.bicep` (simplified single-file stack):

```bicep
@description('Azure region')
param location string = resourceGroup().location

@description('Environment name')
@allowed(['lab', 'dev', 'prod'])
param environment string = 'lab'

@description('Admin SSH public key')
param adminPublicKey string

@description('Unique suffix for globally unique names')
param uniqueSuffix string = uniqueString(resourceGroup().id)

var vmName = 'vm-handbook-${environment}'
var storageName = 'st${uniqueSuffix}'
var kvName = 'kv-${uniqueSuffix}'

resource vnet 'Microsoft.Network/virtualNetworks@2023-09-01' = {
  name: 'vnet-handbook-${environment}'
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: ['10.40.0.0/16']
    }
    subnets: [
      {
        name: 'subnet-web'
        properties: {
          addressPrefix: '10.40.1.0/24'
        }
      }
    ]
  }
  tags: {
    Project: 'devops-handbook'
    Environment: environment
  }
}

resource nsg 'Microsoft.Network/networkSecurityGroups@2023-09-01' = {
  name: 'nsg-web-${environment}'
  location: location
  properties: {
    securityRules: [
      {
        name: 'Allow-SSH'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '22'
        }
      }
      {
        name: 'Allow-HTTP'
        properties: {
          priority: 110
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: '*'
          destinationPortRange: '80'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
        }
      }
    ]
  }
}

resource pip 'Microsoft.Network/publicIPAddresses@2023-09-01' = {
  name: 'pip-${vmName}'
  location: location
  sku: { name: 'Standard' }
  properties: {
    publicIPAllocationMethod: 'Static'
  }
}

resource nic 'Microsoft.Network/networkInterfaces@2023-09-01' = {
  name: 'nic-${vmName}'
  location: location
  properties: {
    ipConfigurations: [
      {
        name: 'ipconfig1'
        properties: {
          subnet: { id: vnet.properties.subnets[0].id }
          privateIPAllocationMethod: 'Dynamic'
          publicIPAddress: { id: pip.id }
        }
      }
    ]
    networkSecurityGroup: { id: nsg.id }
  }
}

resource vm 'Microsoft.Compute/virtualMachines@2023-09-01' = {
  name: vmName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    hardwareProfile: {
      vmSize: 'Standard_B1s'
    }
    osProfile: {
      computerName: vmName
      adminUsername: 'azureuser'
      linuxConfiguration: {
        disablePasswordAuthentication: true
        ssh: {
          publicKeys: [
            {
              path: '/home/azureuser/.ssh/authorized_keys'
              keyData: adminPublicKey
            }
          ]
        }
      }
    }
    storageProfile: {
      imageReference: {
        publisher: 'Canonical'
        offer: '0001-com-ubuntu-server-jammy'
        sku: '22_04-lts-gen2'
        version: 'latest'
      }
      osDisk: {
        createOption: 'FromImage'
        managedDisk: {
          storageAccountType: 'StandardSSD_LRS'
        }
      }
    }
    networkProfile: {
      networkInterfaces: [
        { id: nic.id }
      ]
    }
  }
  tags: {
    Project: 'devops-handbook'
    Environment: environment
  }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
  }
}

resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: kvName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: []  // prefer RBAC — see role assignment below
    enableRbacAuthorization: true
    enabledForTemplateDeployment: true
  }
}

resource kvSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(kv.id, vm.id, 'Secrets User')
  scope: kv
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: vm.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

output vmPublicIp string = pip.properties.ipAddress
output storageAccountName string = storage.name
output keyVaultUri string = kv.properties.vaultUri
output vmPrincipalId string = vm.identity.principalId
```

Deploy locally before pipeline:

```bash
export LAB_RG=rg-devops-handbook-capstone
export LAB_LOCATION=eastus

az group create --name $LAB_RG --location $LAB_LOCATION \
  --tags Project=devops-handbook Environment=lab

PUB_KEY=$(cat ~/.ssh/azure_handbook_ed25519.pub)

az deployment group what-if \
  --resource-group $LAB_RG \
  --template-file infra/main.bicep \
  --parameters adminPublicKey="$PUB_KEY" environment=lab

az deployment group create \
  --resource-group $LAB_RG \
  --template-file infra/main.bicep \
  --parameters adminPublicKey="$PUB_KEY" environment=lab \
  --name main-$(date +%Y%m%d%H%M)
```

---

## 3. Key Vault secret (manual step)

```bash
KV_NAME=$(az keyvault list -g $LAB_RG --query "[0].name" -o tsv)

az keyvault secret set \
  --vault-name $KV_NAME \
  --name app-config \
  --value "handbook-day7-$(date +%F)"

# VM identity can read (RBAC assigned in Bicep)
az keyvault secret show --vault-name $KV_NAME --name app-config --query id -o tsv
```

On VM with managed identity + `az login --identity`, fetch secret without storing keys on disk.

---

## 4. Azure DevOps project & service connection

### Create project (portal or CLI extension)

```bash
az extension add --name azure-devops 2>/dev/null || true
export AZURE_DEVOPS_EXT_PAT=your_pat   # User settings → Personal access tokens

az devops configure --defaults organization=https://dev.azure.com/YOUR_ORG project=devops-handbook

az devops project create --name devops-handbook --visibility private
```

### Federated credential (OIDC) — preferred over client secret

In Entra ID → App registrations → your pipeline app → **Certificates & secrets** → **Federated credentials**:

| Field | Value |
|-------|-------|
| Issuer | `https://vstoken.dev.azure.com/{org-id}` |
| Subject | `sc://YOUR_ORG/devops-handbook/handbook-azure-oidc` |

Create service connection in Azure DevOps:

1. Project Settings → Service connections → New → **Azure Resource Manager**.
2. Choose **Workload Identity federation (manual)** or automatic OIDC wizard.
3. Scope to resource group `rg-devops-handbook-capstone`.

Name it `handbook-azure-oidc` for pipeline YAML below.

---

## 5. Pipeline YAML

`.azuredevops/azure-pipelines.yml`:

```yaml
trigger:
  branches:
    include:
      - main
  paths:
    include:
      - infra/*

variables:
  azureServiceConnection: handbook-azure-oidc
  resourceGroup: rg-devops-handbook-capstone
  location: eastus

stages:
  - stage: Validate
    jobs:
      - job: WhatIf
        pool:
          vmImage: ubuntu-latest
        steps:
          - task: AzureCLI@2
            displayName: Bicep what-if
            inputs:
              azureSubscription: $(azureServiceConnection)
              scriptType: bash
              scriptLocation: inlineScript
              inlineScript: |
                set -euo pipefail
                az group create --name $(resourceGroup) --location $(location) --tags Project=devops-handbook || true
                az deployment group what-if \
                  --resource-group $(resourceGroup) \
                  --template-file infra/main.bicep \
                  --parameters adminPublicKey="$(ADMIN_SSH_PUBLIC_KEY)" environment=lab

  - stage: Deploy
    dependsOn: Validate
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployInfra
        environment: handbook-lab
        pool:
          vmImage: ubuntu-latest
        strategy:
          runOnce:
            deploy:
              steps:
                - checkout: self
                - task: AzureCLI@2
                  displayName: Deploy Bicep
                  inputs:
                    azureSubscription: $(azureServiceConnection)
                    scriptType: bash
                    scriptLocation: inlineScript
                    inlineScript: |
                      set -euo pipefail
                      az deployment group create \
                        --resource-group $(resourceGroup) \
                        --template-file infra/main.bicep \
                        --parameters adminPublicKey="$(ADMIN_SSH_PUBLIC_KEY)" environment=lab \
                        --name main-$(Build.BuildId)
                      IP=$(az deployment group show \
                        --resource-group $(resourceGroup) \
                        --name main-$(Build.BuildId) \
                        --query properties.outputs.vmPublicIp.value -o tsv)
                      echo "##vso[task.setvariable variable=VM_PUBLIC_IP]$IP"
                - task: AzureCLI@2
                  displayName: Smoke test HTTP
                  inputs:
                    azureSubscription: $(azureServiceConnection)
                    scriptType: bash
                    scriptLocation: inlineScript
                    inlineScript: |
                      az vm run-command invoke \
                        --resource-group $(resourceGroup) \
                        --name vm-handbook-lab \
                        --command-id RunShellScript \
                        --scripts "apt-get update && apt-get install -y nginx && echo pipeline-ok > /var/www/html/index.html"
                      sleep 10
                      curl -sf "http://$(VM_PUBLIC_IP)/" | grep pipeline-ok
```

Store `ADMIN_SSH_PUBLIC_KEY` as a **secret variable** in pipeline library or variable group.

---

## 6. GitHub Actions alternative (snippet)

If you use GitHub instead of Azure DevOps:

```yaml
permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      - run: |
          az deployment group create \
            -g rg-devops-handbook-capstone \
            -f infra/main.bicep \
            -p adminPublicKey="${{ secrets.ADMIN_SSH_PUBLIC_KEY }}" environment=lab \
            -n main-${{ github.run_id }}
```

Configure federated credential with issuer `https://token.actions.githubusercontent.com` and subject `repo:ORG/REPO:ref:refs/heads/main`.

---

## 7. Environments, approvals, and drift

| Control | Tool |
|---------|------|
| PR validation | `what-if` job on every pull request |
| Prod gate | Azure DevOps **environment** with manual approval |
| Drift detection | Scheduled pipeline + `what-if` reporting changes |
| State | Azure RM is source of truth (no separate tfstate) |
| Module reuse | Bicep modules in `infra/modules/` |

Detect manual portal edits:

```bash
az deployment group what-if \
  --resource-group rg-devops-handbook-capstone \
  --template-file infra/main.bicep \
  --parameters adminPublicKey="$PUB_KEY" environment=lab \
  | grep -E '^\s+\+|\s+\-|\s+\~' || echo "No drift detected"
```

---

## 8. Budget and cost alerts

```bash
SUB_ID=$(az account show --query id -o tsv)

az consumption budget create \
  --budget-name budget-handbook-lab \
  --amount 25 \
  --time-grain Monthly \
  --start-date $(date +%Y-%m-01) \
  --end-date $(date -v+1y +%Y-%m-01 2>/dev/null || date -d '+1 year' +%Y-%m-01) \
  --resource-group $LAB_RG \
  --category Cost \
  --notifications '{"Actual_GreaterThan_80_Percent":{"enabled":true,"operator":"GreaterThan","threshold":80,"contactEmails":["you@example.com"]}}' \
  2>/dev/null || echo "Use portal: Cost Management → Budgets if CLI scope differs"
```

Review **Cost Management → Cost analysis** filtered by tag `Project=devops-handbook`.

---

## 9. Tagging & Azure Policy (intro)

Required tags policy (assign at RG or subscription):

```bash
# Built-in: require tag on resources — search and assign via portal or:
az policy definition list --query "[?contains(displayName,'require tag')].{Name:displayName, Id:id}" -o table
```

Enforce in landing zones:

- `Environment`, `Owner`, `CostCenter`, `Project`
- Deny public storage accounts (`Deny-Storage-Account-Public-Access`)

---

## 10. Incident runbook template

Save as `RUNBOOK.md` in your repo:

```markdown
## Symptom: Web app unreachable

1. Check Azure Status — region outage?
2. `az vm get-instance-view -g rg-devops-handbook-capstone -n vm-handbook-lab`
3. Metric alert history in Monitor → Alerts
4. KQL: Heartbeat | where Computer contains "vm-handbook"
5. NSG effective rules on NIC
6. Rollback: redeploy previous Bicep deployment name from `az deployment group list`
7. Escalate if storage/Key Vault RBAC changed in Activity Log
```

---

## 11. Lab — Day 7 (capstone)

1. Create `infra/main.bicep` from section 2; deploy with `what-if` then `create`.
2. Store a secret in Key Vault; confirm VM managed identity has **Key Vault Secrets User**.
3. Create Azure DevOps project + OIDC service connection scoped to capstone RG.
4. Add pipeline YAML; set `ADMIN_SSH_PUBLIC_KEY` variable; run pipeline on `main`.
5. Verify smoke test passes (`pipeline-ok` on public IP).
6. Create monthly budget alert email.
7. Execute **full teardown** below.

**Success criteria:** Pipeline green end-to-end; budget configured; all capstone resources deleted.

---

## 12. Full teardown

```bash
# Delete capstone RG (removes nested resources)
az group delete --name rg-devops-handbook-capstone --yes --no-wait

# Original lab RG from Days 1–6
az group delete --name rg-devops-handbook --yes --no-wait

# Service principal from Day 2
SP_APP_ID=$(az ad sp list --display-name sp-devops-handbook-lab --query "[0].appId" -o tsv)
[ -n "$SP_APP_ID" ] && az ad sp delete --id "$SP_APP_ID"

# Verify empty
az group list --query "[?contains(name,'handbook')].name" -o tsv
```

---

## 13. What you learned (Week 1 recap)

| Day | Skill |
|-----|-------|
| 1 | CLI, subscriptions, resource groups |
| 2 | RBAC, service principals, managed identity |
| 3 | VMs, disks, cloud-init, run command |
| 4 | VNet, NSG, public IP, effective rules |
| 5 | Storage, data-plane RBAC, Bicep intro |
| 6 | Log Analytics, KQL, alerts, diagnostics |
| 7 | Pipeline-driven IaC, Key Vault, production hygiene |

### Next steps (optional tracks)

- **AKS handbook extension** — containers on Azure Kubernetes Service
- **Terraform azurerm** — same architecture with HCL state
- **Azure Landing Zones** — enterprise-scale subscription design
- Compare with [AWS handbook](../../aws/README.md) Week 2 for parallel cloud fluency

---

## 14. Key takeaways

- **what-if before every deploy** — treat it like `terraform plan`.
- **OIDC / federated credentials** beat long-lived SP secrets in CI.
- **Delete resource groups** when labs end — the cheapest FinOps habit.

**Previous:** [Day 6](../day6/) · **Handbook home:** [Azure README](../README.md)
