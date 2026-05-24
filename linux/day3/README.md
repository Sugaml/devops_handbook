# Day 3 — Processes, systemd & Job Scheduling

**Goal:** Inspect and control running workloads, manage services with systemd, read logs, and schedule recurring tasks—the operational core of Linux servers and Kubernetes nodes.

**Time:** 5–7 hours

---

## 1. Process fundamentals

Every running program is a **process** with a PID (process ID), parent PID (PPID), user, and state.

```bash
ps                          # snapshot of your session
ps aux                      # all processes, BSD style
ps -ef                      # all processes, UNIX style
ps aux --sort=-%mem | head  # top memory consumers
ps -p 1234 -o pid,ppid,user,cmd,stat,%cpu,%mem

# Process tree
pstree -p
ps -ejH | column -t         # forest view

# Find process by name
pgrep nginx
pgrep -u www-data -a nginx  # show full command line
pidof nginx
```

**Process states (STAT):** `R` running, `S` sleeping, `D` uninterruptible I/O, `Z` zombie, `T` stopped.

```bash
# Zombie investigation
ps aux | awk '$8 ~ /Z/ {print}'
# Fix: kill/restart parent process, not the zombie
```

---

## 2. Signals and killing processes

```bash
kill -l                     # list signals
kill 1234                   # default SIGTERM (15) — graceful
kill -9 1234                # SIGKILL — cannot be caught, use last resort
kill -HUP 1234              # SIGHUP — many daemons reload config
killall nginx
pkill -f "python app.py"

# Graceful nginx reload pattern
sudo kill -HUP $(cat /var/run/nginx.pid)
# or with systemd (preferred)
sudo systemctl reload nginx
```

**DevOps:** Rolling deploys send SIGTERM; apps must handle graceful shutdown (drain connections, finish in-flight work).

---

## 3. Interactive monitoring

```bash
top                         # q quit, M sort by memory, P by CPU, 1 all CPUs
htop                        # nicer UI (install separately)

# Batch mode for scripts
top -b -n 1 | head -20
ps aux --sort=-%cpu | head -10

# Per-process open files and limits
lsof -p 1234
lsof -i :8080               # what's listening on port 8080
lsof +D /var/log            # files open under directory

# File descriptor limits
ulimit -a
cat /proc/1234/limits
```

---

## 4. `/proc` — live process data

```bash
cat /proc/loadavg
cat /proc/meminfo | head
cat /proc/cpuinfo | grep processor | wc -l   # logical CPUs
cat /proc/1234/status | grep -E 'Name|State|VmRSS'
ls -l /proc/1234/fd
cat /proc/1234/cmdline | tr '\0' ' '
```

---

## 5. systemd — service management

systemd is the init system on most modern Linux distros (RHEL 7+, Ubuntu 16.04+, Debian 8+).

```bash
# Unit types: service, socket, timer, mount, target
systemctl list-units --type=service --state=running
systemctl status nginx
systemctl status sshd       # name varies: ssh vs sshd

# Lifecycle
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
sudo systemctl reload nginx
sudo systemctl try-reload-or-restart nginx

# Boot behavior
sudo systemctl enable nginx
sudo systemctl disable nginx
sudo systemctl is-enabled nginx
sudo systemctl is-active nginx

# Failed units (first check in incidents)
systemctl --failed
systemctl reset-failed

# Dependencies
systemctl list-dependencies nginx
systemctl show nginx -p MainPID -p ActiveState
```

### Unit file locations

| Path | Purpose |
|------|---------|
| `/usr/lib/systemd/system/` | Package-installed units |
| `/etc/systemd/system/` | Admin overrides and custom units |
| `/etc/systemd/system/foo.service.d/` | Drop-in overrides |

```bash
# After editing unit files
sudo systemctl daemon-reload
sudo systemctl restart foo

# Edit with drop-in (preferred over replacing vendor unit)
sudo systemctl edit nginx
# creates /etc/systemd/system/nginx.service.d/override.conf
```

### Minimal custom service example

```bash
sudo tee /etc/systemd/system/hello.service <<'EOF'
[Unit]
Description=Hello DevOps Demo
After=network.target

[Service]
Type=simple
User=nobody
ExecStart=/usr/bin/python3 -m http.server 8888 --bind 127.0.0.1
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now hello
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8888/
sudo systemctl stop hello
```

---

## 6. journalctl — systemd logs

```bash
journalctl                    # all logs (pager)
journalctl -u nginx           # specific unit
journalctl -u nginx -f        # follow
journalctl -u nginx --since "1 hour ago"
journalctl -u nginx --since today --until "30 min ago"
journalctl -p err             # priority err and above
journalctl -k                   # kernel messages
journalctl -b                   # current boot
journalctl -b -1                # previous boot
journalctl --disk-usage
sudo journalctl --vacuum-size=500M
```

Traditional logs still exist: `/var/log/syslog`, `/var/log/messages`, app-specific under `/var/log/`.

```bash
dmesg | tail                    # kernel ring buffer
dmesg -T                        # human timestamps (if supported)
dmesg | grep -i oom             # out-of-memory killer
```

---

## 7. Cron and systemd timers

### cron

```bash
crontab -l                    # current user's crontab
sudo crontab -l -u root

# Format: min hour dom month dow command
# Edit
crontab -e

# Example entries
# Every 5 minutes
*/5 * * * * /opt/scripts/healthcheck.sh >> /var/log/health.log 2>&1
# Daily at 2:30 AM
30 2 * * * /opt/scripts/backup.sh
# Weekdays at 9 AM
0 9 * * 1-5 /opt/scripts/report.sh

# System-wide
ls /etc/cron.d/
cat /etc/crontab
ls /etc/cron.{hourly,daily,weekly,monthly}/
```

```bash
# Run once at specific time
echo "/opt/script.sh" | at 02:00 tomorrow
atq
atrm 1
```

### systemd timers (preferred for new automation)

```bash
# Example timer unit
sudo tee /etc/systemd/system/backup.timer <<'EOF'
[Unit]
Description=Run backup daily

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo tee /etc/systemd/system/backup.service <<'EOF'
[Unit]
Description=Backup job

[Service]
Type=oneshot
ExecStart=/opt/scripts/backup.sh
EOF

sudo systemctl enable --now backup.timer
systemctl list-timers --all
```

---

## 8. Background jobs and `nohup`

```bash
long_running_cmd &            # background
jobs
fg %1
bg %1

nohup ./deploy.sh > deploy.log 2>&1 &
disown                          # detach from shell

# screen/tmux for persistent sessions
tmux new -s ops
# Ctrl-b d detach; tmux attach -t ops
```

---

## 9. Resource control (cgroups via systemd)

```bash
# Slice limits in unit file
# MemoryMax=512M
# CPUQuota=50%

systemd-cgtop                   # live cgroup usage
systemctl show hello.service -p MemoryCurrent -p CPUUsageNSec
```

On Kubernetes nodes, kubelet uses cgroups to enforce pod limits—same kernel mechanism.

---

## 10. Lab — Day 3

1. Find the top 5 processes by CPU and by memory; record PID and command.
2. Identify what listens on port 22: `ss -tlnp | grep :22` or `sudo lsof -i :22`.
3. Create and enable the `hello.service` from section 5; verify with `systemctl status` and `journalctl -u hello`.
4. Add a cron entry that appends `date` to `/tmp/cron-test.log` every minute; verify after 2 minutes.
5. Simulate failure: start a service with wrong `ExecStart`; use `systemctl status` and `journalctl` to diagnose.

**Stretch:** Convert the cron job to a systemd timer.

---

## 11. DevOps connections

- **Kubernetes:** `kubectl logs` vs node-level `journalctl -u kubelet` when pods fail to start.
- **Deploys:** `systemctl reload` vs `restart` affects connection draining.
- **On-call:** `systemctl --failed` + `journalctl -p err -b` is a standard first triage sequence.

---

## Quick reference

| Task | Command |
|------|---------|
| All processes | `ps aux` |
| Kill gracefully | `kill PID` |
| Service status | `systemctl status UNIT` |
| Follow service logs | `journalctl -u UNIT -f` |
| Enable on boot | `systemctl enable UNIT` |
| User cron | `crontab -e` |
| List timers | `systemctl list-timers` |

**Previous:** [Day 2](../day2/) · **Next:** [Day 4 — Package management](../day4/)
