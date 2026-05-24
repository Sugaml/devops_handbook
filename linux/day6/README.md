# Day 6 — Storage, LVM & Backups

**Goal:** Manage disks and mounts, extend storage with LVM, archive and compress data, and implement backup/restore patterns used in production DevOps.

**Time:** 5–7 hours

---

## 1. Block devices and partitioning

```bash
lsblk                           # tree view of disks and partitions
lsblk -f                        # filesystems and UUIDs
sudo fdisk -l                   # partition tables
sudo parted -l

# Identify disk vs partition
# /dev/sda = whole disk, /dev/sda1 = first partition
# NVMe: /dev/nvme0n1, /dev/nvme0n1p1

# UUID (preferred in /etc/fstab)
blkid
findmnt -S UUID=xxxx-xxxx
```

**Warning:** `fdisk`, `parted`, and `mkfs` on wrong device cause data loss. Always confirm with `lsblk` and hostname.

---

## 2. Filesystems and mounting

```bash
# Create ext4 (lab disk only)
sudo mkfs.ext4 /dev/sdb1
sudo mkfs.xfs /dev/sdb1           # common on RHEL

# Mount temporarily
sudo mkdir -p /mnt/data
sudo mount /dev/sdb1 /mnt/data
mount | grep /mnt/data
findmnt /mnt/data

# Unmount (must not be busy)
sudo umount /mnt/data
sudo fuser -vm /mnt/data          # who is using it
sudo lsof +D /mnt/data

# Persistent mount: /etc/fstab
# UUID=abc-123  /mnt/data  ext4  defaults,nofail  0  2
sudo cp /etc/fstab /etc/fstab.bak
sudo nano /etc/fstab
sudo mount -a                     # test fstab without reboot
```

**fstab fields:** device, mountpoint, type, options, dump, fsck order.

Useful options: `nofail` (boot without disk), `noatime`, `defaults`.

---

## 3. Disk usage analysis

```bash
df -h
df -i                             # inodes — "No space left" with free GB often means inode exhaustion
df -hT                            # include filesystem type

du -sh /var/log
du -h --max-depth=1 /var | sort -hr
du -xh /home | sort -hr | tail -20

# ncdu — interactive (install separately)
ncdu /var
```

**DevOps:** Log volume full → deploy fails; monitor `df` and rotate logs before disk alerts.

---

## 4. LVM — Logical Volume Manager

LVM layers: **PV** (physical volume) → **VG** (volume group) → **LV** (logical volume) → filesystem.

```bash
# Inspect
sudo pvs
sudo vgs
sudo lvs
sudo lvdisplay

# Create stack (lab empty disk /dev/sdb)
sudo pvcreate /dev/sdb
sudo vgcreate vg_data /dev/sdb
sudo lvcreate -L 10G -n lv_app vg_data
sudo mkfs.ext4 /dev/vg_data/lv_app
sudo mount /dev/vg_data/lv_app /mnt/app

# Extend logical volume (online grow common in prod)
sudo lvextend -L +5G /dev/vg_data/lv_app
# ext4:
sudo resize2fs /dev/vg_data/lv_app
# xfs:
sudo xfs_growfs /mnt/app

# Add another disk to volume group
sudo pvcreate /dev/sdc
sudo vgextend vg_data /dev/sdc
sudo lvextend -l +100%FREE /dev/vg_data/lv_app
sudo resize2fs /dev/vg_data/lv_app
```

**DevOps:** Cloud volumes attach as new block devices; LVM or direct mount + grow filesystem is standard for database and log partitions.

---

## 5. Swap

```bash
free -h
swapon --show
cat /proc/swaps

# Temporary swap file (example)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Kubernetes nodes often disable swap or require explicit configuration—know your platform policy.

---

## 6. Archiving and compression

```bash
# tar — tape archive (no compression by default)
tar cf archive.tar dir/
tar czf archive.tar.gz dir/       # gzip
tar cjf archive.tar.bz2 dir/      # bzip2
tar cJf archive.tar.xz dir/       # xz — smaller, slower

# Extract
tar xzf archive.tar.gz
tar xzf archive.tar.gz -C /dest/path
tar tf archive.tar.gz             # list contents

# Preserve permissions (important for backups)
tar czpf backup.tar.gz /etc/nginx
tar xzpf backup.tar.gz -C /restore/

# zip
zip -r backup.zip folder/
unzip backup.zip -d /restore/

# Single file compression
gzip file.txt                     # creates file.txt.gz, removes original
gunzip file.txt.gz
zcat file.txt.gz | head
```

---

## 7. Backup strategies with rsync and tar

### rsync incremental-style

```bash
BACKUP_ROOT=/backup/host-$(hostname -s)
DATE=$(date +%Y%m%d)

sudo mkdir -p "$BACKUP_ROOT/$DATE"
sudo rsync -aAXv --delete \
  --exclude={"/dev/*","/proc/*","/sys/*","/tmp/*","/run/*","/mnt/*","/media/*","/lost+found"} \
  / "$BACKUP_ROOT/$DATE/"

# --delete mirrors source (dangerous if source empty — use safeguards)
```

### Database-friendly pattern

```bash
# Dump then archive
mysqldump -u root mydb | gzip > /backup/mydb-$(date +%F).sql.gz
pg_dump mydb | gzip > /backup/mydb-$(date +%F).sql.gz
```

### Retention

```bash
find /backup -maxdepth 1 -type d -mtime +30 -exec rm -rf {} +
```

---

## 8. Restore verification (often skipped — don't)

```bash
# Test tar integrity
tar tzf backup.tar.gz > /dev/null && echo OK

# Restore single file
tar xzf backup.tar.gz path/to/file.conf

# Compare checksums
find /etc/nginx -type f -exec md5sum {} \; | sort > /tmp/before.md5
# after restore
find /etc/nginx -type f -exec md5sum {} \; | sort > /tmp/after.md5
diff /tmp/before.md5 /tmp/after.md5
```

Use `sha256sum` for stronger hashing in security-sensitive contexts.

---

## 9. iSCSI/NFS basics (shared storage awareness)

```bash
# NFS mount example
showmount -e nfs-server.example.com
sudo mount -t nfs nfs-server.example.com:/export /mnt/nfs
grep nfs /etc/fstab

# iSCSI initiator (RHEL tools)
sudo dnf install iscsi-initiator-utils
sudo systemctl enable --now iscsid
sudo iscsiadm -m discovery -t sendtargets -p 10.0.0.5:3260
sudo iscsiadm -m node --login
lsblk   # new disk appears
```

Kubernetes PVs often back onto NFS, EBS, or CSI drivers—node storage CLI still applies for troubleshooting.

---

## 10. SMART and disk health

```bash
sudo dnf install smartmontools   # or apt install smartmontools
sudo smartctl -a /dev/sda
sudo smartctl -H /dev/sda         # health pass/fail
```

---

## 11. Lab — Day 6

Use loop devices if no spare disk:

```bash
# Create 500MB loop "disk" for practice
dd if=/dev/zero of=/tmp/lab-disk.img bs=1M count=500
sudo losetup -fP /tmp/lab-disk.img
LOOP=$(losetup -j | grep lab-disk | cut -d: -f1)
echo "Loop device: $LOOP"
sudo fdisk $LOOP                  # create one Linux partition
sudo partprobe $LOOP
sudo mkfs.ext4 ${LOOP}p1
sudo mkdir -p /mnt/lab
sudo mount ${LOOP}p1 /mnt/lab
echo test | sudo tee /mnt/lab/file.txt
sudo umount /mnt/lab
```

Tasks:

1. Run `df -h` and `lsblk -f`; explain root filesystem device.
2. Find top 5 largest directories under `/var`.
3. Create a tarball of `/etc/ssh` preserving permissions; extract to `/tmp/restore-ssh`.
4. Write a one-line backup script using `tar czf` with date in filename.
5. Verify tarball with `tar tzf`.

**Stretch:** Walk through LVM commands on paper for "add 20GB EBS volume and extend `/var`".

---

## 12. DevOps connections

- **Immutable infra:** Backups matter for stateful services (DBs, registries), not ephemeral app servers.
- **Velero/restic:** Same concepts—snapshots, retention, restore drills.
- **Incidents:** Full disk on `/var` or `/` stops Docker and kubelet—`df`/`du` first.

---

## Quick reference

| Task | Command |
|------|---------|
| Disk layout | `lsblk -f` |
| Space usage | `df -h`, `du -sh` |
| Mount | `mount`, `/etc/fstab` |
| LVM extend | `lvextend` + `resize2fs`/`xfs_growfs` |
| Archive | `tar czpf` |
| Sync backup | `rsync -aAX` |

**Previous:** [Day 5](../day5/) · **Next:** [Day 7 — Scripting & automation](../day7/)
