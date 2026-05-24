# Day 7 — Bash Scripting, Automation & Production Troubleshooting

**Goal:** Write reliable shell scripts, automate operational tasks, follow a structured troubleshooting methodology, and tie Linux skills into DevOps workflows.

**Time:** 6–8 hours

---

## 1. Script fundamentals

```bash
#!/usr/bin/env bash
# Always use shebang; env finds bash in PATH

set -euo pipefail
# -e  exit on error
# -u  error on unset variable
# -o pipefail  pipeline fails if any command fails

IFS=$'\n\t'                     # safer word splitting (optional hardening)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/myapp/deploy.log"
```

```bash
# Make executable
chmod +x deploy.sh
./deploy.sh
bash -x deploy.sh               # debug trace
shellcheck deploy.sh            # static analysis (install shellcheck)
```

---

## 2. Variables, arguments, and exit codes

```bash
#!/usr/bin/env bash
set -euo pipefail

ENV="${1:-staging}"             # default staging
VERSION="${2:?Usage: $0 ENV VERSION}"   # required arg

echo "Deploying $VERSION to $ENV"

# Special variables
echo "Script: $0"
echo "Args: $#"
echo "All: $*"
echo "Last exit: $?"

# Exit with status
exit 0    # success
exit 1    # generic failure
```

**DevOps:** CI systems key off exit codes—always `exit 1` on failure paths.

---

## 3. Conditionals and tests

```bash
# File tests
[[ -f /etc/nginx/nginx.conf ]] && echo "exists"
[[ -d /var/log ]] || { echo "missing log dir"; exit 1; }
[[ -x ./script.sh ]] || chmod +x ./script.sh
[[ -s file.txt ]]                 # non-empty file

# String and numeric
[[ "$ENV" == "prod" ]] && echo "careful"
[[ "$DISK_PCT" -gt 90 ]] && echo "disk critical"

# Command success
if systemctl is-active --quiet nginx; then
  echo "nginx running"
else
  echo "nginx down"; exit 1
fi

# case
case "$ENV" in
  dev|staging) REPLICAS=1 ;;
  prod)        REPLICAS=3 ;;
  *) echo "unknown env"; exit 1 ;;
esac
```

---

## 4. Loops and functions

```bash
# for
for svc in nginx redis mysql; do
  systemctl is-active "$svc" || echo "$svc not active"
done

for i in {1..5}; do echo "attempt $i"; done

# while read (safe line processing)
while IFS= read -r line; do
  echo "Line: $line"
done < /etc/hosts

# functions
log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

deploy_app() {
  local version="$1"
  log "Starting deploy $version"
  # ...
}

deploy_app "1.2.3"
```

---

## 5. Error handling and traps

```bash
#!/usr/bin/env bash
set -euo pipefail

cleanup() {
  local code=$?
  [[ -n "${TEMP_DIR:-}" && -d "$TEMP_DIR" ]] && rm -rf "$TEMP_DIR"
  exit "$code"
}
trap cleanup EXIT

TEMP_DIR=$(mktemp -d)
# work in TEMP_DIR; cleanup runs on exit or error

# Ignore failure for specific command
set +e
optional_check || true
set -e
```

---

## 6. Practical DevOps scripts

### Health check

```bash
#!/usr/bin/env bash
set -euo pipefail

URL="${1:-http://127.0.0.1:8080/health}"
TIMEOUT=5

code=$(curl -sf -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$URL" || echo "000")

if [[ "$code" == "200" ]]; then
  echo "OK $URL"
  exit 0
else
  echo "FAIL $URL status=$code"
  exit 1
fi
```

### Disk alert

```bash
#!/usr/bin/env bash
set -euo pipefail

THRESHOLD="${1:-90}"

df -hP | awk -v t="$THRESHOLD" 'NR>1 {
  gsub(/%/,"",$5)
  if ($5+0 >= t) print "WARN", $6, "used", $5"%"
}'
```

### Parallel host check

```bash
#!/usr/bin/env bash
set -euo pipefail

HOSTS=(web1 web2 web3)

check_host() {
  local h=$1
  if ping -c 1 -W 2 "$h" &>/dev/null; then
    echo "$h UP"
  else
    echo "$h DOWN" >&2
    return 1
  fi
}

export -f check_host
printf '%s\n' "${HOSTS[@]}" | xargs -P 3 -I{} bash -c 'check_host "$@"' _ {}
```

---

## 7. Logging and observability hooks

```bash
exec > >(tee -a "$LOG_FILE") 2>&1   # tee stdout/stderr to file

logger -t myapp "deploy started"     # syslog
journalctl -t myapp

# Structured-ish log line (JSON)
log_json() {
  printf '{"ts":"%s","level":"%s","msg":"%s"}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$2"
}
log_json INFO "deploy_complete"
```

---

## 8. systemd integration for scripts

```bash
# /etc/systemd/system/app-deploy.service
[Unit]
Description=Application deploy
After=network-online.target

[Service]
Type=oneshot
User=deploy
Environment=APP_ENV=production
ExecStart=/opt/scripts/deploy.sh production "${VERSION}"
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Trigger via CI over SSH:

```bash
ssh deploy@prod "sudo systemctl start app-deploy.service"
ssh deploy@prod "journalctl -u app-deploy -n 50 --no-pager"
```

---

## 9. Troubleshooting methodology

Use a consistent order—avoids random guessing under pressure.

```
1. What changed?     (deploy, config, patch, traffic)
2. Scope?            (one host, all hosts, one region)
3. Symptoms?         (latency, errors, down)
4. Quick health:     uptime, df, free, systemctl --failed
5. Logs:            journalctl, app logs, load balancer
6. Network:         ss, curl, dig
7. Process:         ps, top, strace (last resort)
8. Mitigate → root cause → fix → postmortem
```

### First-5-minutes command bundle

```bash
uptime
df -h
free -h
systemctl --failed
journalctl -p err -b --no-pager | tail -50
ss -s
dmesg | tail -20
```

### Deeper tools

```bash
# strace — syscalls (noisy, short runs)
sudo strace -p PID -f -e trace=network,file 2>&1 | head -100

# perf (if installed)
sudo perf top

# Core dumps (when app crashes)
ulimit -c unlimited
coredumpctl list
```

---

## 10. Security hygiene in scripts

```bash
# Never hardcode secrets
API_TOKEN="${API_TOKEN:?set API_TOKEN env var}"

# Quote variables
rm -rf "${TARGET_DIR:?}/"   # :? prevents rm -rf / if TARGET_DIR empty

# Avoid eval with untrusted input
# Use mktemp not predictable /tmp names for multi-user systems
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT

# Restrict permissions on output
install -m 600 -o root root /path/to/secret.conf /etc/app/
```

---

## 11. Capstone lab — Day 7

Build **`/opt/devops-lab/day7/deploy.sh`** that:

1. Accepts `ENV` and `VERSION` arguments with validation.
2. Uses `set -euo pipefail` and `shellcheck`-clean patterns.
3. Writes timestamped logs to `/var/log/devops-deploy.log` (or `/tmp` if non-root).
4. Checks disk usage; warns if any mount ≥ 85%.
5. Performs a HTTP health check against `http://127.0.0.1:8080/health` (mock with `python3 -m http.server` if needed).
6. Exits non-zero on failure.

Optional:

- Wrap in a systemd oneshot unit.
- Add a `rollback.sh` that restores from Day 6 tarball pattern.

---

## 12. 7-day review cheat sheet

| Area | Key commands |
|------|----------------|
| Files | `ls`, `find`, `chmod`, `chown` |
| Text | `grep`, `sed`, `awk`, `jq` |
| Processes | `ps`, `top`, `kill`, `lsof` |
| Services | `systemctl`, `journalctl` |
| Packages | `apt` / `dnf`, `dpkg` / `rpm` |
| Network | `ip`, `ss`, `curl`, `dig`, `ssh`, `rsync` |
| Storage | `lsblk`, `df`, `du`, `tar`, LVM |
| Automation | bash + `set -euo pipefail`, systemd |

---

## 13. DevOps next steps

- **Configuration management:** Ansible modules mirror every CLI from Days 1–7.
- **Containers:** Linux namespaces/cgroups underpin Docker; node troubleshooting returns to this handbook.
- **Kubernetes:** Worker node skills = Linux + `kubectl`; control plane still runs on Linux.
- **Observability:** Prometheus node_exporter exposes metrics for the same resources you inspected manually.

---

## Quick reference

| Task | Pattern |
|------|---------|
| Safe script header | `set -euo pipefail` |
| Required arg | `${1:?message}` |
| Temp dir | `mktemp -d` + trap |
| Lint script | `shellcheck script.sh` |
| On-call triage | `uptime; df; free; systemctl --failed; journalctl -p err -b` |

**Previous:** [Day 6](../day6/) · **Back to overview:** [Linux handbook](../)

---

## Congratulations

You have a full week of Linux CLI depth aligned with real DevOps work. Revisit labs on a fresh VM monthly; speed and confidence come from repetition, not reading alone.
