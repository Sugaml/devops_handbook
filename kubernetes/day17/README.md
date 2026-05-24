# Day 17 — StorageClasses & Dynamic Provisioning

**Goal:** Provision storage on demand with StorageClasses, parameters, and volume expansion; understand cloud-specific provisioners.

**Time:** 4 hours

---

## 1. Dynamic provisioning flow

```
PVC created → StorageClass → provisioner → PV created & bound automatically
```

```bash
kubectl get storageclass
kubectl describe storageclass standard
```

---

## 2. StorageClass manifest

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs   # cloud-specific
parameters:
  type: gp3
  fsType: ext4
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer   # delay until Pod scheduled
```

kind default uses `rancher.io/local-path` or similar — check with `kubectl get sc`.

---

## 3. Default StorageClass

```yaml
metadata:
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
```

Only one default recommended.

```yaml
# PVC omitting storageClassName uses default
spec:
  resources:
    requests:
      storage: 1Gi
  accessModes:
    - ReadWriteOnce
```

---

## 4. Volume expansion

```yaml
allowVolumeExpansion: true
```

```bash
kubectl patch pvc web-data -n handbook-lab -p '{"spec":{"resources":{"requests":{"storage":"5Gi"}}}}'
kubectl get pvc web-data -n handbook-lab -w
# File system resize may need pod restart or in-place resize
```

---

## 5. Volume binding modes

| Mode | Behavior |
|------|----------|
| **Immediate** | PV provisioned when PVC created |
| **WaitForFirstConsumer** | Waits for Pod using PVC — better for topology-aware zones |

---

## 6. Snapshots (CSI)

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: web-data-snap
  namespace: handbook-lab
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: web-data
```

Requires CSI driver with snapshot support — standard on EKS/GKE production.

---

## 7. Lab — Day 17

1. Inspect default StorageClass on your cluster; note provisioner and reclaimPolicy.
2. Create PVC without `storageClassName`; verify dynamic PV appears.
3. If expansion supported, grow PVC from 2Gi to 3Gi; verify bound capacity.
4. Create second StorageClass (non-default) with different name; bind PVC explicitly.
5. Read CSI driver docs for your target cloud (even if lab is kind).

**Stretch:** Take VolumeSnapshot if CSI snapshot controller installed.

---

## 8. DevOps connections

- **IaC:** Terraform creates StorageClasses and disk types per environment.
- **Goldilocks / rightsizing:** Oversized PVCs waste money on cloud disks.
- **Multi-AZ:** WaitForFirstConsumer + topology keys for zone-aligned disks.

---

## Quick reference

| Task | Command |
|------|---------|
| List SC | `kubectl get storageclass` |
| Default SC | annotation `is-default-class` |
| Expand PVC | patch `spec.resources.requests.storage` |
| Provisioner | `kubectl describe sc NAME` |

**Next:** [Day 18 — Helm](../day18/)
