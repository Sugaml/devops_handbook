# Day 24 — Cluster Lifecycle: Upgrades, Backups & DR

**Goal:** Plan Kubernetes upgrades, backup etcd and workloads with Velero, implement PodDisruptionBudgets, and document disaster recovery.

**Time:** 5–6 hours

---

## 1. Upgrade strategy

```
Control plane first → node pools → add-ons (CNI, CSI, ingress) → workloads
```

| Component | Notes |
|-----------|-------|
| Managed (EKS/GKE) | Provider upgrades API server; you upgrade node pools |
| kubeadm | `kubeadm upgrade plan/apply` |
| Skew policy | kubelet within 2 minor versions of API server |

Always read release notes and deprecation warnings before upgrade.

```bash
kubectl get nodes -o wide
kubectl version
kubeadm upgrade plan   # if self-managed
```

---

## 2. Node maintenance

```bash
kubectl drain NODE_NAME --ignore-daemonsets --delete-emptydir-data
# perform maintenance / upgrade kubelet
kubectl uncordon NODE_NAME
```

Drain respects PodDisruptionBudgets — may block if PDB too strict.

---

## 3. PodDisruptionBudget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web-pdb
  namespace: handbook-lab
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: web
```

Or `maxUnavailable: 1`. Protects voluntary disruptions (drain, cluster upgrade).

---

## 4. Velero backups

```bash
# Install Velero CLI + server (example with kind/minio lab)
velero install \
  --provider aws \
  --bucket velero \
  --secret-file ./credentials-velero

velero backup create handbook-backup --include-namespaces handbook-lab
velero backup describe handbook-backup
velero schedule create daily --schedule="0 2 * * *" --include-namespaces handbook-lab
velero restore create --from-backup handbook-backup
```

Backs up Kubernetes objects + optional PV snapshots via CSI.

---

## 5. etcd backup (self-managed)

```bash
# On control plane (kubeadm)
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-$(date +%F).db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

Managed clusters: provider handles etcd; you focus on workload backup.

---

## 6. Disaster recovery runbook outline

1. **RTO/RPO** targets per tier
2. Restore cluster or fail over to secondary region
3. Restore Velero backups / DB dumps
4. DNS cutover
5. Validate probes and smoke tests
6. Post-incident review

---

## 7. Lab — Day 24

1. Create PDB for `web` Deployment (minAvailable 1); drain a worker node; observe behavior.
2. Install Velero (or read install docs + simulate with `kubectl get all -o yaml` export).
3. Export all resources in `handbook-lab` to YAML backup file manually.
4. Delete namespace `handbook-lab`; restore from export.
5. Write one-page DR checklist for your lab app.

**Stretch:** Test Velero restore into fresh namespace on kind.

---

## 8. DevOps connections

- **Change windows:** Upgrades + PDB + HPA together affect capacity during drain.
- **Multi-region:** Active-passive clusters with global load balancing.
- **Compliance:** Backup encryption and retention policies.

---

## Quick reference

| Task | Command |
|------|---------|
| Drain node | `kubectl drain NODE --ignore-daemonsets` |
| Uncordon | `kubectl uncordon NODE` |
| PDB | `kubectl get pdb -n NS` |
| Velero backup | `velero backup create NAME` |

**Next:** [Day 25 — Observability](../day25/)
