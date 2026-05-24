# Day 6 — Azure Monitor, Log Analytics, Alerts & Diagnostics

**Goal:** Centralize metrics and logs; query with KQL; configure diagnostic settings and actionable alerts — the observability foundation for SRE work.

**Time:** 4–6 hours

**Services:** Azure Monitor, Log Analytics, Application Insights, Action Groups

---

## 1. Observability stack map

| Layer | Azure service | DevOps use |
|-------|---------------|------------|
| **Metrics** | Azure Monitor metrics | CPU, disk, HTTP failures — dashboards & alerts |
| **Logs** | Log Analytics workspace | KQL queries, correlation across resources |
| **APM / traces** | Application Insights | Request latency, dependencies, exceptions |
| **Alerts** | Metric / log / activity alerts | PagerDuty, email, webhooks |
| **Diagnostics** | Diagnostic settings | Route platform logs to Log Analytics or Storage |

Data flows:

```
Resource (VM, Storage, AKS) → Diagnostic settings → Log Analytics workspace
                              → Metrics → Alert rules → Action group
App code → Application Insights SDK / agent → same workspace (often)
```

---

## 2. Create Log Analytics workspace

```bash
export LAB_RG=rg-devops-handbook
export LAB_LOCATION=eastus
export WORKSPACE=law-handbook

az monitor log-analytics workspace create \
  --resource-group $LAB_RG \
  --workspace-name $WORKSPACE \
  --location $LAB_LOCATION \
  --retention-time 30 \
  --tags Project=devops-handbook Day=6

WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group $LAB_RG --workspace-name $WORKSPACE --query customerId -o tsv)

echo "Workspace ID: $WORKSPACE_ID"
```

---

## 3. Azure Monitor Agent on VM (data collection)

For a VM from Day 3/4 (or create a small one):

```bash
export VM_NAME=vm-handbook-day3   # or vm-handbook-net

# Enable Azure Monitor Agent via DCR (Data Collection Rule) — modern path
DCR_NAME=dcr-handbook-vm

az monitor data-collection rule create \
  --resource-group $LAB_RG \
  --name $DCR_NAME \
  --location $LAB_LOCATION \
  --kind Linux \
  --data-flows '[{"streams":["Microsoft-InsightsMetrics","Microsoft-Syslog"],"destinations":["law"]}]' \
  --destinations "{\"logAnalytics\":[{\"workspaceResourceId\":\"$(az monitor log-analytics workspace show -g $LAB_RG -n $WORKSPACE --query id -o tsv)\",\"name\":\"law\"}]}" \
  --data-sources "{\"syslog\":[{\"name\":\"syslog\",\"streams\":[\"Microsoft-Syslog\"],\"facilityNames\":[\"*\"],\"logLevels\":[\"*\"]}]}"

# Associate DCR with VM
az monitor data-collection rule association create \
  --resource-group $LAB_RG \
  --rule-name $DCR_NAME \
  --name dcr-assoc-vm \
  --target-resource $(az vm show -g $LAB_RG -n $VM_NAME --query id -o tsv)
```

Generate syslog traffic on VM:

```bash
VM_IP=$(az vm show -d -g $LAB_RG -n $VM_NAME --query publicIps -o tsv)
ssh -i ~/.ssh/azure_handbook_ed25519 azureuser@$VM_IP \
  'logger "handbook-day6 test message"; sudo systemctl restart ssh'
```

Wait 2–5 minutes for ingestion.

---

## 4. KQL basics (Log Analytics)

Open portal → Log Analytics workspace → **Logs**, or use CLI:

```bash
az monitor log-analytics query \
  --workspace $WORKSPACE_ID \
  --analytics-query "Heartbeat | summarize LastSeen=max(TimeGenerated) by Computer | order by LastSeen desc" \
  -o table
```

### Essential queries

```kusto
// VMs reporting heartbeat (AMA installed)
Heartbeat
| where TimeGenerated > ago(24h)
| summarize LastHeartbeat=max(TimeGenerated) by Computer
| order by LastHeartbeat desc

// Syslog errors last hour
Syslog
| where TimeGenerated > ago(1h)
| where SeverityLevel in ("err", "crit", "alert", "emerg")
| project TimeGenerated, Computer, Facility, SyslogMessage
| order by TimeGenerated desc

// Storage transactions (after diagnostic settings — section 6)
StorageBlobLogs
| where TimeGenerated > ago(1h)
| summarize count() by OperationName, StatusCode
```

Save useful queries as **query packs** or in repo `.kql` files for reuse in incidents.

---

## 5. Application Insights (web/API workload)

```bash
export APPINSIGHTS=appi-handbook

az monitor app-insights component create \
  --app $APPINSIGHTS \
  --location $LAB_LOCATION \
  --resource-group $LAB_RG \
  --workspace $WORKSPACE \
  --tags Project=devops-handbook Day=6

CONN_STRING=$(az monitor app-insights component show \
  --app $APPINSIGHTS --resource-group $LAB_RG \
  --query connectionString -o tsv)

echo "Connection string (redact in notes): ${CONN_STRING:0:40}..."
```

Instrument a simple app (Node example on VM or laptop):

```javascript
// npm install applicationinsights
const appInsights = require('applicationinsights');
appInsights.setup(process.env.APPLICATIONINSIGHTS_CONNECTION_STRING).start();
```

Query requests in portal or KQL:

```kusto
requests
| where timestamp > ago(1h)
| summarize count(), avg(duration) by name
| order by count_ desc
```

---

## 6. Diagnostic settings (platform logs)

Send storage account logs to Log Analytics:

```bash
STORAGE_NAME=$(az storage account list -g $LAB_RG --query "[0].name" -o tsv)
STORAGE_ID=$(az storage account show -g $LAB_RG -n $STORAGE_NAME --query id -o tsv)
LAW_ID=$(az monitor log-analytics workspace show -g $LAB_RG -n $WORKSPACE --query id -o tsv)

az monitor diagnostic-settings create \
  --name diag-storage-to-law \
  --resource $STORAGE_ID \
  --workspace $LAW_ID \
  --logs '[{"category":"StorageRead","enabled":true},{"category":"StorageWrite","enabled":true}]' \
  --metrics '[{"category":"Transaction","enabled":true}]'
```

Activity Log (subscription events) — subscription-scoped:

```bash
SUB_ID=$(az account show --query id -o tsv)

az monitor diagnostic-settings subscription create \
  --name diag-activity-to-law \
  --subscription $SUB_ID \
  --workspace $LAW_ID \
  --logs '[{"category":"Administrative","enabled":true},{"category":"Alert","enabled":true}]'
```

---

## 7. Metrics and charts

```bash
# VM CPU percentage — last hour
az monitor metrics list \
  --resource $(az vm show -g $LAB_RG -n $VM_NAME --query id -o tsv) \
  --metric "Percentage CPU" \
  --interval PT1M \
  --aggregation Average \
  --offset 1h \
  -o table
```

Portal: **Monitor → Metrics** — pin charts to shared dashboards for on-call.

---

## 8. Action groups and alerts

### Action group (notification target)

```bash
export ACTION_GROUP=ag-handbook-oncall
YOUR_EMAIL="you@example.com"

az monitor action-group create \
  --resource-group $LAB_RG \
  --name $ACTION_GROUP \
  --short-name handbook \
  --action email admin $YOUR_EMAIL \
  --tags Project=devops-handbook
```

### Metric alert — high CPU

```bash
az monitor metrics alert create \
  --resource-group $LAB_RG \
  --name alert-vm-cpu-high \
  --scopes $(az vm show -g $LAB_RG -n $VM_NAME --query id -o tsv) \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action $(az monitor action-group show -g $LAB_RG -n $ACTION_GROUP --query id -o tsv) \
  --description "Lab: VM CPU sustained above 80%" \
  --severity 2
```

### Log alert — heartbeat missing

```bash
az monitor scheduled-query create \
  --resource-group $LAB_RG \
  --name alert-heartbeat-missing \
  --scopes $LAW_ID \
  --condition-query "Heartbeat | summarize Last=max(TimeGenerated) by Computer | where Last < ago(15m)" \
  --condition "count 'Computer' > 0" \
  --condition-window 15m \
  --evaluation-frequency 5m \
  --action-groups $(az monitor action-group show -g $LAB_RG -n $ACTION_GROUP --query id -o tsv) \
  --description "VM stopped sending heartbeat"
```

Stress-test CPU briefly to validate metric alert:

```bash
ssh -i ~/.ssh/azure_handbook_ed25519 azureuser@$VM_IP \
  'sudo apt-get install -y stress-ng; stress-ng --cpu 2 --timeout 120s'
```

---

## 9. Workbooks and dashboards (portal)

1. Monitor → **Workbooks** → New — combine metrics + logs + Activity Log.
2. Pin KQL chart to **Azure Dashboard** shared with team.

Export workbook JSON to git for reviewable observability-as-code (optional stretch).

---

## 10. DevOps production patterns

| Practice | Implementation |
|----------|------------------|
| Single workspace per env | `law-prod`, `law-nonprod` — avoid mixing prod logs in lab workspace |
| Alert fatigue | Alert on **symptoms** (SLO burn) not every CPU spike |
| Correlation ID | Pass `trace_id` from ingress → app → dependencies |
| Retention vs cost | 30d hot in workspace; archive to Storage for compliance |
| CI validation | `az monitor scheduled-query create` in Bicep; review in PR |

---

## 11. Lab — Day 6

1. Create Log Analytics workspace `law-handbook` with 30-day retention.
2. Associate DCR with your lab VM; confirm `Heartbeat` rows in KQL.
3. Create Application Insights linked to the same workspace.
4. Add diagnostic settings on a storage account (blob read/write logs).
5. Create action group with your email; metric alert on CPU > 80%.
6. Trigger `stress-ng`; confirm alert email (may take 5–10 min).

**Success criteria:** KQL returns Heartbeat/Syslog; you receive at least one alert notification.

---

## 12. Teardown

```bash
az monitor metrics alert delete -g $LAB_RG -n alert-vm-cpu-high
az monitor scheduled-query delete -g $LAB_RG -n alert-heartbeat-missing
az monitor action-group delete -g $LAB_RG -n $ACTION_GROUP
az monitor app-insights component delete -g $LAB_RG --app $APPINSIGHTS
# Keep workspace for Day 7 or delete:
# az monitor log-analytics workspace delete -g $LAB_RG -n $WORKSPACE --yes
```

---

## 13. Key takeaways

- **Log Analytics + KQL** is the query engine for most Azure logs.
- **Diagnostic settings** must be explicit — platform logs are not collected by default.
- Design alerts with **runbooks** linked in the action group (URL field).

**Previous:** [Day 5](../day5/) · **Next:** [Day 7 — Bicep, CI/CD & production](../day7/)
