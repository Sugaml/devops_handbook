# Day 5 — Storage Accounts, Blobs & ARM/Bicep Basics

**Goal:** Work with Azure Storage (blob, file, queue, table); understand control plane vs data plane RBAC; deploy your first Bicep template.

**Time:** 4–6 hours

**Services:** Storage, Resource Manager, Bicep

---

## 1. Storage account fundamentals

| Concept | Notes |
|---------|-------|
| **Storage account** | Globally unique name, 3–24 lowercase letters/numbers |
| **Container** | Blob namespace (like S3 bucket prefix grouping) |
| **Blob types** | Block (files), append (logs), page (legacy VHDs) |
| **Replication** | LRS, ZRS, GRS, GZRS — LRS cheapest for labs |
| **Access tier** | Hot, Cool, Archive — Hot for frequent access |
| **Endpoint** | `https://{account}.blob.core.windows.net` |

**Control plane** (`Microsoft.Storage/storageAccounts/*`) vs **data plane** (`Storage Blob Data Contributor`) — apps reading blobs need data plane RBAC or keys/SAS.

---

## 2. Create storage account

```bash
export LAB_RG=rg-devops-handbook
export LAB_LOCATION=eastus

# Name must be globally unique — add random suffix
STORAGE_NAME="handbook$(openssl rand -hex 3)"
echo "Storage account: $STORAGE_NAME"

az storage account create \
  --resource-group $LAB_RG \
  --name $STORAGE_NAME \
  --location $LAB_LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --access-tier Hot \
  --https-only true \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false \
  --tags Project=devops-handbook Day=5

az storage account show --resource-group $LAB_RG --name $STORAGE_NAME \
  --query "{Name:name, SKU:sku.name, Endpoints:primaryEndpoints}" -o jsonc
```

---

## 3. Blob operations (CLI)

```bash
# Use Azure AD login for data plane (recommended)
export AZURE_STORAGE_ACCOUNT=$STORAGE_NAME

az storage container create --name logs --auth-mode login
az storage container create --name artifacts --auth-mode login

# Upload file
echo "handbook day5 $(date -u +%FT%TZ)" > /tmp/handbook-day5.txt
az storage blob upload \
  --account-name $STORAGE_NAME \
  --container-name logs \
  --name day5/handbook-day5.txt \
  --file /tmp/handbook-day5.txt \
  --auth-mode login \
  --overwrite

# List blobs
az storage blob list \
  --account-name $STORAGE_NAME \
  --container-name logs \
  --prefix day5/ \
  --auth-mode login \
  --query "[].{Name:name, Size:properties.contentLength, Modified:properties.lastModified}" -o table

# Download
az storage blob download \
  --account-name $STORAGE_NAME \
  --container-name logs \
  --name day5/handbook-day5.txt \
  --file /tmp/downloaded.txt \
  --auth-mode login
cat /tmp/downloaded.txt
```

If `AuthorizationPermissionMismatch`, assign yourself **Storage Blob Data Contributor** on the account:

```bash
USER_OID=$(az ad signed-in-user show --query id -o tsv)
STORAGE_ID=$(az storage account show -g $LAB_RG -n $STORAGE_NAME --query id -o tsv)

az role assignment create \
  --assignee-object-id $USER_OID \
  --assignee-principal-type User \
  --role "Storage Blob Data Contributor" \
  --scope "$STORAGE_ID"
# Wait 1–2 minutes, retry blob upload
```

---

## 4. Shared Access Signatures (SAS) — time-limited access

```bash
# Account SAS (lab — prefer user delegation SAS in prod)
EXPIRY=$(date -u -v+1d +%Y-%m-%dT%H:%MZ 2>/dev/null || date -u -d '+1 day' +%Y-%m-%dT%H:%MZ)

az storage account generate-sas \
  --account-name $STORAGE_NAME \
  --services b \
  --resource-types sco \
  --permissions rwdlac \
  --expiry "$EXPIRY" \
  --https-only \
  -o tsv
```

Use SAS in external tools when Azure AD is not available — rotate and scope tightly.

---

## 5. Static website hosting

```bash
az storage blob service-properties update \
  --account-name $STORAGE_NAME \
  --static-website \
  --index-document index.html \
  --404-document 404.html \
  --auth-mode login

echo '<html><body><h1>Handbook Day 5</h1></body></html>' > /tmp/index.html
az storage blob upload \
  --account-name $STORAGE_NAME \
  --container-name '$web' \
  --name index.html \
  --file /tmp/index.html \
  --auth-mode login \
  --content-type text/html

# Primary web endpoint
az storage account show -g $LAB_RG -n $STORAGE_NAME \
  --query primaryEndpoints.web -o tsv
```

Front with **Azure CDN** or **Front Door** in production for TLS on custom domains.

---

## 6. ARM vs Bicep

| Format | Description |
|--------|-------------|
| **ARM JSON** | Native Azure Resource Manager template |
| **Bicep** | DSL that compiles to ARM — preferred for humans |

Install Bicep:

```bash
az bicep install
az bicep version
```

---

## 7. First Bicep template

Create `storage.bicep`:

```bicep
@description('Region for resources')
param location string = resourceGroup().location

@description('Base name for storage account (must be unique globally)')
param storageAccountName string

@description('Tags applied to all resources')
param tags object = {
  Project: 'devops-handbook'
  Day: '5'
}

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  tags: tags
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storage
  name: 'default'
}

resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'artifacts'
  properties: {
    publicAccess: 'None'
  }
}

output storageAccountId string = storage.id
output blobEndpoint string = storage.properties.primaryEndpoints.blob
```

Parameters file `storage.bicepparam`:

```bicep
using 'storage.bicep'

param storageAccountName = 'handbookbicep001'  // change to unique name
param location = 'eastus'
```

Deploy:

```bash
cd azure/day5/labs
# storage.bicep and storage.bicepparam are in this folder

UNIQUE_NAME="handbookbicep$(openssl rand -hex 2)"

az deployment group validate \
  --resource-group rg-devops-handbook \
  --template-file storage.bicep \
  --parameters storageAccountName=$UNIQUE_NAME

az deployment group create \
  --resource-group rg-devops-handbook \
  --template-file storage.bicep \
  --parameters storageAccountName=$UNIQUE_NAME \
  --name deploy-storage-day5

az deployment group show \
  --resource-group rg-devops-handbook \
  --name deploy-storage-day5 \
  --query properties.provisioningState -o tsv
```

Preview changes before apply:

```bash
az deployment group what-if \
  --resource-group rg-devops-handbook \
  --template-file storage.bicep \
  --parameters storageAccountName=$UNIQUE_NAME
```

---

## 8. ARM template export (learning aid)

Export existing RG state to see what Azure built:

```bash
az group export --resource-group rg-devops-handbook > /tmp/exported-rg.json
# Large JSON — use jq to inspect resource types
jq '[.resources[].type] | unique' /tmp/exported-rg.json
```

Do not treat exports as production IaC without cleanup — names and dependencies need refactoring.

---

## 9. Lab — Day 5

1. Create storage account `$STORAGE_NAME` with public blob access **disabled**.
2. Assign yourself **Storage Blob Data Contributor**; upload a file to `logs/day5/` using `--auth-mode login`.
3. Enable static website; upload `index.html`; open web endpoint in browser.
4. Write and deploy `storage.bicep` with a **unique** account name via `az deployment group create`.
5. Run `what-if` before a second deployment that adds a tag change.

**Success criteria:** Blob upload works with Azure AD auth; Bicep deployment succeeds with `Succeeded` state.

---

## 10. Teardown

```bash
# Delete Bicep-deployed account (replace name)
# az storage account delete -g rg-devops-handbook -n handbookbicepXXXX --yes

az storage account delete -g rg-devops-handbook -n $STORAGE_NAME --yes
```

---

## 11. Key takeaways

- Storage account names are **global**; plan naming conventions with random suffixes or hash.
- Use **data plane RBAC** or managed identity for apps — not account keys in config files.
- **Bicep + what-if** is the baseline IaC workflow before CI/CD (Day 7).

**Previous:** [Day 4](../day4/) · **Next:** [Day 6 — Monitor & Log Analytics](../day6/)
