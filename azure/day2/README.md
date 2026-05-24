# Day 2 — Entra ID, RBAC, Service Principals & Managed Identity

**Goal:** Model identity and authorization in Azure; assign RBAC roles, create a service principal for automation, and attach a managed identity to a VM.

**Time:** 4–6 hours

**Services:** Microsoft Entra ID, Azure RBAC

---

## 1. Identity building blocks

| Entity | Purpose | Long-lived secret? |
|--------|---------|-------------------|
| **User** | Human (UPN login) | Password / MFA |
| **Group** | Bundle members for RBAC | No |
| **Service principal** | App/automation identity in Entra ID | Client secret or cert (avoid in prod) |
| **Managed identity** | Azure-managed SP for resources | No — platform rotates |
| **Role definition** | Set of allowed actions | JSON permissions |
| **Role assignment** | Bind role to identity at scope | — |

**Scope hierarchy** (assign least privilege at the narrowest scope):

```
Management group → Subscription → Resource group → Resource
```

---

## 2. RBAC vs Entra ID roles

| System | Controls | Example |
|--------|----------|---------|
| **Azure RBAC** | Who can manage **Azure resources** | Contributor on `rg-devops-handbook` |
| **Entra ID roles** | Who can manage **directory** | Global Administrator, User Administrator |

DevOps engineers spend most time in **Azure RBAC**.

### Common built-in roles

| Role | Typical use |
|------|-------------|
| **Owner** | Full access + assign roles — avoid for daily work |
| **Contributor** | Create/manage resources — no RBAC assignment |
| **Reader** | Read-only — good for observability accounts |
| **User Access Administrator** | Manage RBAC only |
| **Storage Blob Data Contributor** | Data plane for blobs (not just control plane) |

List roles:

```bash
az role definition list --query "[?roleName=='Contributor'].{Name:roleName, Id:id}" -o table
```

---

## 3. Check your effective access

```bash
# Who am I in Entra ID?
az ad signed-in-user show \
  --query "{Name:displayName, UPN:userPrincipalName, Id:id}" -o table

# Role assignments for current user at subscription scope
SUB_ID=$(az account show --query id -o tsv)
az role assignment list \
  --assignee $(az ad signed-in-user show --query id -o tsv) \
  --scope "/subscriptions/$SUB_ID" \
  --query "[].{Role:roleDefinitionName, Scope:scope}" -o table
```

---

## 4. Assign RBAC at resource group scope

```bash
export LAB_RG=rg-devops-handbook
RG_ID=$(az group show --name $LAB_RG --query id -o tsv)

# Assign Reader to another user (replace UPN) — lab with a colleague or second account
COLLEAGUE_UPN="colleague@contoso.com"
COLLEAGUE_OID=$(az ad user show --id "$COLLEAGUE_UPN" --query id -o tsv)

az role assignment create \
  --assignee-object-id "$COLLEAGUE_OID" \
  --assignee-principal-type User \
  --role Reader \
  --scope "$RG_ID"

# List assignments on the RG
az role assignment list --resource-group $LAB_RG \
  --query "[].{Principal:principalName, Role:roleDefinitionName}" -o table

# Remove assignment
az role assignment delete \
  --assignee "$COLLEAGUE_OID" \
  --role Reader \
  --scope "$RG_ID"
```

**DevOps note:** RBAC changes can take **1–5 minutes** to propagate. Retry with `sleep 30` in scripts if you get `AuthorizationFailed`.

---

## 5. Custom role (least privilege)

Create `reader-vm.json` — read VMs only in one RG:

```json
{
  "Name": "DevOps Handbook VM Reader",
  "IsCustom": true,
  "Description": "Read VMs and disks in assigned scope",
  "Actions": [
    "Microsoft.Compute/virtualMachines/read",
    "Microsoft.Compute/disks/read"
  ],
  "NotActions": [],
  "AssignableScopes": [
    "/subscriptions/SUBSCRIPTION_ID/resourceGroups/rg-devops-handbook"
  ]
}
```

Replace `SUBSCRIPTION_ID`, then:

```bash
SUB_ID=$(az account show --query id -o tsv)
sed "s/SUBSCRIPTION_ID/$SUB_ID/" reader-vm.json > /tmp/reader-vm-patched.json

az role definition create --role-definition /tmp/reader-vm-patched.json

az role definition list --custom-role-only true \
  --query "[?roleName=='DevOps Handbook VM Reader']" -o table
```

---

## 6. Service principal for CI/CD

Service principals are Entra ID application identities used by scripts and pipelines.

```bash
# Create SP with Contributor on lab RG only (narrow scope)
RG_ID=$(az group show --name rg-devops-handbook --query id -o tsv)

az ad sp create-for-rbac \
  --name sp-devops-handbook-lab \
  --role Contributor \
  --scopes "$RG_ID" \
  --output json
```

Save output — **client secret is shown once**:

```json
{
  "appId": "...",
  "displayName": "sp-devops-handbook-lab",
  "password": "...",
  "tenant": "..."
}
```

Login as the SP:

```bash
az login --service-principal \
  --username APP_ID \
  --password CLIENT_SECRET \
  --tenant TENANT_ID

az account show -o table
az group list -o table   # should see lab RG only if scoped correctly

# Return to user login
az logout
az login
```

List and clean up:

```bash
az ad sp list --display-name sp-devops-handbook-lab -o table
SP_APP_ID=$(az ad sp list --display-name sp-devops-handbook-lab --query "[0].appId" -o tsv)

# Delete SP when done (Day 7 teardown)
az ad sp delete --id "$SP_APP_ID"
```

**Production:** Prefer **federated credentials** (GitHub/OIDC) over client secrets (Day 7).

---

## 7. Managed identity (system-assigned)

Managed identities eliminate secrets for workloads running on Azure.

We prepare here; full VM attach happens on Day 3:

```bash
# Conceptual — VM created on Day 3
# az vm create ... --assign-identity

# After VM exists:
VM_NAME=vm-handbook-day3
PRINCIPAL_ID=$(az vm show --resource-group rg-devops-handbook --name $VM_NAME \
  --query identity.principalId -o tsv)

# Grant SP access to storage (preview for Day 5)
STORAGE_ID=$(az storage account show --name STORAGE_NAME --resource-group rg-devops-handbook --query id -o tsv)

az role assignment create \
  --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Data Reader" \
  --scope "$STORAGE_ID"
```

On the VM, the IMDS endpoint provides tokens:

```bash
# From inside Azure VM (Day 3 lab)
curl -s 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/' \
  -H Metadata:true | jq -r .access_token | head -c 40
echo "..."
```

---

## 8. Conditional Access & MFA (production)

Portal path (conceptual — enforced by security team):

1. Entra ID → Security → Conditional Access.
2. Require MFA for all users except break-glass accounts.
3. Block legacy authentication.

DevOps impact: service principals bypass MFA but should use **certificates or OIDC**; humans use MFA always.

---

## 9. Lab — Day 2

1. Run `az ad signed-in-user show` and list your role assignments on the subscription.
2. Create service principal `sp-devops-handbook-lab` with **Contributor** scoped **only** to `rg-devops-handbook`.
3. `az login --service-principal` and verify you can list the lab RG but cannot create RGs at subscription scope.
4. Log out SP; log back in as yourself.
5. Create custom role `DevOps Handbook VM Reader` (or skip if no second user to assign).
6. Document SP credentials in a **local password manager** — never commit to git.

**Success criteria:** SP works with narrow scope; you understand RBAC vs Entra ID admin roles.

**Stretch:** Assign **Reader** at subscription scope to yourself on a second subscription in a sandbox tenant — compare scopes.

---

## 10. Key takeaways

- Assign RBAC at the **smallest scope** that works.
- **Service principals** for external automation; **managed identities** for Azure-hosted workloads.
- Wait for RBAC propagation; design pipelines with retries.

**Previous:** [Day 1](../day1/) · **Next:** [Day 3 — Virtual machines & disks](../day3/)
