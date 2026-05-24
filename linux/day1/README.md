# Day 1 — Linux Fundamentals: Filesystem, Navigation & Permissions

**Goal:** Navigate the filesystem confidently, understand FHS layout, and manage permissions—the foundation for every server, container host, and CI runner.

**Time:** 4–6 hours (theory + hands-on)

---

## 1. Filesystem Hierarchy Standard (FHS)

| Path | Purpose | DevOps note |
|------|---------|-------------|
| `/` | Root of entire tree | Never casually `chmod` here |
| `/etc` | Config files | Version-control critical configs |
| `/var` | Variable data (logs, caches, spool) | Log rotation lives here |
| `/tmp` | Temporary files | Often `noexec` on hardened hosts |
| `/home` | User home directories | SSH keys in `~/.ssh` |
| `/opt` | Optional third-party software | Vendor agents, tools |
| `/usr` | User programs, libraries | Most binaries in `/usr/bin` |
| `/sbin`, `/usr/sbin` | Admin binaries | `ip`, `fdisk`, `systemctl` |
| `/proc`, `/sys` | Kernel interfaces | Debugging CPU, memory, mounts |
| `/dev` | Device files | Disks as `/dev/sda`, etc. |

```bash
# See mount points and filesystem types
findmnt
# or
mount | column -t

# Disk usage by top-level directory
sudo du -xh --max-depth=1 / 2>/dev/null | sort -hr | head -20
```

---

## 2. Navigation & file operations

### Present location and listing

```bash
pwd                          # print working directory
cd /var/log                  # absolute path
cd ..                        # parent directory
cd -                         # previous directory (toggle)
cd ~                         # home directory

ls                           # list (often aliased to ls --color)
ls -la                       # all files + long format
ls -lah                      # human-readable sizes
ls -lt                       # sort by modification time
ls -lS                       # sort by size
ls -R /etc/nginx 2>/dev/null # recursive (can be huge)

# tree (install if missing)
tree -L 2 /etc
```

### Create, copy, move, delete

```bash
mkdir -p /tmp/devops-lab/{app,logs,config}
touch /tmp/devops-lab/app/version.txt
echo "1.0.0" > /tmp/devops-lab/app/version.txt

cp file.txt file.txt.bak
cp -r /etc/nginx /tmp/nginx-backup    # recursive directory copy
cp -a /source/dir /dest/dir           # archive mode: preserve links, perms, times

mv oldname.txt newname.txt
mv /tmp/file.txt /tmp/devops-lab/logs/

rm file.txt                   # remove file (no undo)
rm -i *.log                   # interactive
rm -rf /tmp/devops-lab        # recursive force — double-check path!

# Safe pattern: preview then delete
ls -d /tmp/devops-lab/*
rm -rf /tmp/devops-lab
```

### Viewing file content

```bash
cat /etc/os-release
less /var/log/syslog          # q to quit, /pattern to search
head -n 20 /var/log/auth.log
tail -n 50 /var/log/auth.log
tail -f /var/log/nginx/access.log   # follow (essential for incidents)

wc -l /etc/passwd             # line count
file /usr/bin/python3         # detect file type
stat /etc/passwd              # inode, permissions, timestamps
```

### Links

```bash
# Hard link (same inode, same filesystem)
ln source.txt hardlink.txt

# Symbolic link (pointer to path)
ln -s /etc/nginx/nginx.conf ~/nginx.conf
ls -l ~/nginx.conf            # shows -> target
readlink -f ~/nginx.conf      # resolve full path
```

---

## 3. Users, groups, and identity

```bash
whoami
id
id deploy                     # uid, gid, groups for user 'deploy'

# Current login sessions
who
w

# User database
getent passwd | tail -5
getent group | grep docker

# Switch user (requires appropriate privileges)
sudo -i                       # root login shell
sudo -u www-data id
su - deploy                   # login shell as deploy
```

**DevOps:** CI runners and app processes often run as dedicated users (`jenkins`, `gitlab-runner`, `nginx`). Principle of least privilege starts with non-root service accounts.

---

## 4. Permissions (rwx) and ownership

### Permission model

```
-rwxr-xr--  1 deploy deploy 4096 May 24 10:00 deploy.sh
 │││││││││
 │││││││└─ other:  r--
 │││││└└└── group:  r-x
 │└└└────── owner:  rwx
 └──────── file type (- file, d directory, l symlink)
```

Numeric mode: `r=4`, `w=2`, `x=1` → `chmod 755` = `rwxr-xr-x`

```bash
chmod 644 config.ini          # rw-r--r--
chmod u+x script.sh           # add execute for owner
chmod g-w secret.env          # remove group write
chmod -R 750 /opt/myapp       # recursive

chown deploy:deploy app/
chown root:root /etc/sudoers   # only root should own sensitive files
chgrp docker deploy           # add user to docker group via usermod typically

# Default permissions for new files
umask                         # e.g. 0022 → files 644, dirs 755
umask 027                       # stricter: group can't read others' files
```

### Special bits (know these for DevOps)

```bash
# setuid / setgid / sticky (see man chmod)
chmod u+s /usr/bin/passwd     # often already set on system binaries
chmod +t /tmp                 # sticky bit on /tmp

ls -ld /tmp                   # drwxrwxrwt
```

### ACLs (when rwx per user/group is not enough)

```bash
# Debian/Ubuntu: apt install acl
getfacl /var/www/html
setfacl -m u:deploy:rwx /var/www/html
setfacl -m g:logs:r-- /var/log/myapp
```

---

## 5. Environment and paths

```bash
echo $PATH
which nginx
type -a python3               # all definitions (alias, function, path)
command -v kubectl

export APP_ENV=staging
export PATH="$HOME/bin:$PATH"
env | sort
printenv APP_ENV
```

Shell config (order matters): `/etc/profile` → `~/.bash_profile` or `~/.profile` → `~/.bashrc` (interactive non-login).

---

## 6. Essential one-liners for Day 1

```bash
# Find largest files in current directory
du -ah . | sort -hr | head -20

# Find files modified in last 24 hours
find . -type f -mtime -1

# Create a file with specific content without editor
cat <<'EOF' > /tmp/devops-lab/config.yaml
app: api
port: 8080
EOF

# Disk space
df -h
df -i                         # inode usage (full inodes = "no space" with free GB)
```

---

## 7. Lab — Day 1

1. Create `/tmp/devops-day1` with subdirs `bin`, `etc`, `logs`.
2. Create a script `bin/healthcheck.sh` that prints hostname and date; make it executable only for your user (`chmod 700`).
3. Create a symlink `etc/app.conf` → `bin/../config.ini` (create `config.ini` with two key=value lines).
4. Run `stat` on the script and explain uid/gid/mode in your own words.
5. Set `umask 077`, create a new file, observe default permissions with `ls -l`.

**Stretch:** On a test file, demonstrate `chmod` using both symbolic (`u+x`) and octal (`755`) forms.

---

## 8. DevOps connections

- **Immutable infra:** You still SSH to debug; navigation and permissions explain why `Permission denied` happens on deploy keys or volume mounts.
- **Containers:** Host paths bind-mounted into pods inherit host permissions; UID mismatches are Day 1 problems in production.
- **Config management:** Ansible/Chef files land in `/etc` with specific owners—`chown`/`chmod` in playbooks mirror today's CLI.

---

## Quick reference

| Task | Command |
|------|---------|
| Where am I? | `pwd` |
| List all details | `ls -lah` |
| Recursive copy preserve attrs | `cp -a` |
| Follow logs | `tail -f` |
| Change owner | `chown user:group` |
| Change mode | `chmod` |
| Default new file mode | `umask` |

**Next:** [Day 2 — Shell, pipes & text processing](../day2/)
