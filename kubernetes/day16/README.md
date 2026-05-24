# Day 16 — PersistentVolumes & PersistentVolumeClaims

**Goal:** Attach durable storage to Pods via PV/PVC, understand access modes and reclaim policies, and bind storage manually or dynamically.

**Time:** 5 hours

---

## 1. Storage concepts

```
PersistentVolume (PV)     — cluster storage resource (admin or dynamic)
PersistentVolumeClaim     — Pod's request for storage
Pod volumeMount           — uses PVC
```

---

## 2. Access modes

| Mode | Abbrev | Meaning |
|------|--------|---------|
| ReadWriteOnce | RWO | One node read/write |
| ReadOnlyMany | ROX | Many nodes read-only |
| ReadWriteMany | RWX | Many nodes read/write |

Cloud block storage (EBS, PD) is usually RWO; NFS/EFS for RWX.

---

## 3. PVC manifest

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: web-data
  namespace: handbook-lab
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 2Gi
  storageClassName: standard   # optional; omit for default
```

```yaml
# Pod/Deployment volume
volumes:
  - name: data
    persistentVolumeClaim:
      claimName: web-data
```

```bash
kubectl apply -f pvc.yaml
kubectl get pvc -n handbook-lab
kubectl describe pvc web-data -n handbook-lab
```

---

## 4. Static PV (admin-provisioned)

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-handbook-1
spec:
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /mnt/data/handbook
    type: DirectoryOrCreate
```

Binding: PVC `storageClassName` + capacity + accessMode must match available PV.

---

## 5. Reclaim policies

| Policy | When PVC deleted |
|--------|------------------|
| **Retain** | PV kept; manual cleanup |
| **Delete** | PV and underlying volume deleted (dynamic) |
| **Recycle** | Deprecated — scrub data |

---

## 6. Troubleshooting

| Status | Meaning |
|--------|---------|
| Pending | No matching PV or provisioner issue |
| Bound | Linked to PV |
| Lost | PV gone |

```bash
kubectl get pv,pvc -n handbook-lab
kubectl describe pvc web-data -n handbook-lab
kubectl get events -n handbook-lab --field-selector involvedObject.name=web-data
```

---

## 7. Lab — Day 16

1. Create PVC `web-data` (2Gi, RWO); mount in nginx Deployment at `/usr/share/nginx/html`.
2. Write `index.html`; delete Pod; verify data persists on new Pod.
3. Scale Deployment to 2 replicas — observe second Pod Pending (RWO conflict) — document why.
4. List PVs and note `storageClassName` from kind default provisioner.
5. Delete Deployment; delete PVC; observe PV status (Deleted or Released).

**Stretch:** Create static PV + PVC with `storageClassName: manual` on kind.

---

## 8. DevOps connections

- **Backups:** Velero, volume snapshots (Day 24) depend on PVC/PV model.
- **StatefulSet:** volumeClaimTemplates auto-create PVC per pod (Day 11).
- **Performance:** Choose SSD vs HDD StorageClass for databases.

---

## Quick reference

| Task | Command |
|------|---------|
| PVC status | `kubectl get pvc -n NS` |
| PV list | `kubectl get pv` |
| Mount | `persistentVolumeClaim.claimName` |
| Access modes | RWO, ROX, RWX |

**Next:** [Day 17 — StorageClasses](../day17/)
