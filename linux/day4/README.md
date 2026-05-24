# Day 4 — Package Management & Software Lifecycle

**Goal:** Install, update, query, and remove software reliably across Debian and RHEL families—how you bootstrap servers, CI images, and golden AMIs.

**Time:** 4–6 hours

---

## 1. Package management landscape

| Family | Format | Low-level tool | High-level tool |
|--------|--------|----------------|-----------------|
| Debian/Ubuntu | `.deb` | `dpkg` | `apt` / `apt-get` |
| RHEL/Rocky/Amazon | `.rpm` | `rpm` | `dnf` (yum legacy) |
| Arch | `.pkg.tar` | `pacman` | — |
| Universal | — | — | Snap, Flatpak |

**DevOps:** Dockerfiles and Packer templates encode the same operations as `RUN apt install` or `dnf install`.

---

## 2. APT (Debian/Ubuntu)

```bash
sudo apt update                 # refresh package index
sudo apt upgrade                # upgrade installed packages
sudo apt full-upgrade           # may remove/install to resolve deps
sudo apt autoremove               # remove unused dependencies
sudo apt clean                    # clear downloaded package cache

# Install / remove
sudo apt install nginx
sudo apt install -y nginx=1.24.*   # pin version (pattern)
sudo apt remove nginx
sudo apt purge nginx              # remove + config files

# Search and info
apt search nginx
apt show nginx
apt list --installed | grep nginx
apt list --upgradable

# Download package without installing
apt download nginx
apt-get source nginx              # source package

# Simulate (dry run)
sudo apt install -s nginx
```

### Repository management

```bash
ls /etc/apt/sources.list /etc/apt/sources.list.d/
cat /etc/apt/sources.list

# Add repo (example: Docker)
# Prefer vendor's signed key + sources.list.d entry
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list
sudo apt update

# Hold package at current version (prevent auto-upgrade)
sudo apt-mark hold nginx
apt-mark showhold
sudo apt-mark unhold nginx
```

### dpkg (low-level)

```bash
dpkg -l | grep nginx
dpkg -L nginx                     # files installed by package
dpkg -S /usr/sbin/nginx           # which package owns file
sudo dpkg -i ./mypackage.deb
sudo apt-get install -f           # fix broken dependencies after manual dpkg -i
```

---

## 3. DNF/YUM (RHEL/Rocky/Amazon Linux)

```bash
sudo dnf check-update
sudo dnf upgrade
sudo dnf install nginx
sudo dnf install -y nginx-1.24.0-*
sudo dnf remove nginx

dnf search nginx
dnf info nginx
dnf list installed nginx
dnf list available nginx

# History (rollback aid)
dnf history
dnf history info 5
sudo dnf history undo 5

# Clean cache
sudo dnf clean all
```

### Repositories

```bash
dnf repolist
dnf repolist -v
ls /etc/yum.repos.d/

# Enable EPEL (example on RHEL/Rocky)
sudo dnf install epel-release
sudo dnf config-manager --set-enabled crb    # Rocky 9 CodeReady Builder

# Module streams (AppStream)
dnf module list
sudo dnf module enable nginx:1.24
dnf module info nginx
```

### rpm (low-level)

```bash
rpm -qa | grep nginx
rpm -ql nginx                     # list files
rpm -qf /usr/sbin/nginx           # query file owner
rpm -ivh package.rpm
rpm -e nginx
rpm -V nginx                      # verify (config changes show as 5 or missing)
```

---

## 4. Comparing distros in scripts

```bash
# Detect family
if [ -f /etc/os-release ]; then
  . /etc/os-release
  echo "$ID $VERSION_ID"
fi

# Portable install pattern (simplified)
case "$ID" in
  ubuntu|debian)
    sudo apt update && sudo apt install -y curl git jq
    ;;
  rhel|rocky|amzn)
    sudo dnf install -y curl git jq
    ;;
  *)
    echo "Unsupported distro: $ID" >&2; exit 1
    ;;
esac
```

---

## 5. Installing from source (when packages lag)

```bash
# Build dependencies (Debian)
sudo apt install -y build-essential libssl-dev

# Typical autotools flow
curl -LO https://example.com/app-1.2.3.tar.gz
tar xzf app-1.2.3.tar.gz && cd app-1.2.3
./configure --prefix=/usr/local
make -j$(nproc)
sudo make install

# Prefer /opt or /usr/local for manual installs
# Document version; use package manager when possible
```

**DevOps:** Prefer vendor repos or containers over ad-hoc `make install` in production.

---

## 6. Snap and alternative packaging

```bash
snap list
sudo snap install kubectl --classic
sudo snap refresh
sudo snap remove kubectl
```

Useful on desktops; servers often avoid snap for core services due to mount/autoupdate behavior.

---

## 7. Security updates and patching workflow

```bash
# Debian — security-only (if security suite configured)
sudo apt upgrade -s | grep -i security

# RHEL — advisories
dnf updateinfo list security
dnf updateinfo summary

# Unattended upgrades (Debian)
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
cat /etc/apt/apt.conf.d/50unattended-upgrades

# dnf-automatic (RHEL family)
sudo dnf install dnf-automatic
sudo systemctl enable --now dnf-automatic.timer
```

**DevOps checklist:**

1. Pin versions in staging; test upgrades before prod.
2. Rebuild golden images on patch cycle.
3. Scan images (Trivy, Grype) after `apt/dnf` changes.

---

## 8. Querying what changed

```bash
# Debian
grep " install " /var/log/dpkg.log | tail
zgrep "status installed" /var/log/dpkg.log*

# RHEL
dnf history | tail
cat /var/log/dnf.log | tail
```

---

## 9. Lab — Day 4

1. Identify your distro with `/etc/os-release`; list all enabled repos.
2. Install `htop`, `tree`, and `jq`; verify with `which` and package query (`dpkg -l` or `rpm -q`).
3. Find which package owns `/usr/bin/curl`.
4. Simulate an upgrade: `apt upgrade -s` or `dnf upgrade --assumeno`.
5. Download a `.deb` or `.rpm` for a small tool with `apt download` / `dnf download` without installing.

**Stretch:** Hold/pin one package; attempt upgrade and confirm it is skipped.

---

## 10. DevOps connections

- **Infrastructure as Code:** Cloud-init and Ansible modules wrap the same APT/DNF operations idempotently.
- **Containers:** Multi-stage builds run `apt-get install` in builder stage; minimize layers and clean cache (`rm -rf /var/lib/apt/lists/*`).
- **Compliance:** `rpm -Va` / configured AIDE jobs detect unauthorized binary changes.

---

## Quick reference

| Task | Debian | RHEL |
|------|--------|------|
| Update index | `apt update` | `dnf check-update` |
| Install | `apt install PKG` | `dnf install PKG` |
| Search | `apt search` | `dnf search` |
| Who owns file? | `dpkg -S` | `rpm -qf` |
| List files in pkg | `dpkg -L` | `rpm -ql` |
| History | `/var/log/dpkg.log` | `dnf history` |

**Previous:** [Day 3](../day3/) · **Next:** [Day 5 — Networking & SSH](../day5/)
