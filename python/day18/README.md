# Day 18 — SSH Automation with Paramiko

**Goal:** Connect to remote Linux hosts over SSH from Python, run commands, upload files, and build small fleet automation scripts — the programmatic counterpart to Ansible ad-hoc commands.

**Time:** 4–5 hours (theory + hands-on)

---

## 1. SSH in DevOps workflows

| Task | Tool choice |
|------|-------------|
| Idempotent config at scale | Ansible (Day 1+) |
| Custom logic, API glue, one-off fleet ops | **Paramiko** |
| Interactive sessions | OpenSSH `ssh` |

Paramiko implements the SSH2 protocol in pure Python — no shelling out to `ssh` required.

```
  Python script  ──►  Paramiko  ──►  SSH daemon  ──►  remote shell
```

---

## 2. Install and basic connection

```bash
pip install paramiko
```

```python
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # lab only

client.connect(
    hostname="192.168.1.10",
    username="ansible",
    key_filename="/Users/you/.ssh/id_ed25519",
    timeout=10,
)

stdin, stdout, stderr = client.exec_command("hostname && uptime")
print(stdout.read().decode())
client.close()
```

**Production:** Use `RejectPolicy` or load known hosts from `~/.ssh/known_hosts` — never `AutoAddPolicy` in prod.

```python
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.RejectPolicy())
```

---

## 3. Running commands and exit codes

```python
def run_command(client: paramiko.SSHClient, command: str, timeout: int = 30) -> dict:
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    return {
        "stdout": stdout.read().decode(),
        "stderr": stderr.read().decode(),
        "exit_code": exit_code,
    }
```

Check `exit_code` — Paramiko does not raise on non-zero exits.

---

## 4. SFTP — upload and download

```python
sftp = client.open_sftp()
sftp.put("/local/path/script.sh", "/tmp/script.sh")
sftp.chmod("/tmp/script.sh", 0o755)
sftp.close()
```

Use SFTP for small config drops; for large trees consider `rsync` via subprocess or S3 intermediate storage.

---

## 5. Multiple hosts with ThreadPoolExecutor

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def check_host(host: str) -> dict:
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    try:
        client.connect(host, username="ansible", key_filename="~/.ssh/id_ed25519", timeout=10)
        result = run_command(client, "uptime")
        return {"host": host, "ok": result["exit_code"] == 0, "output": result["stdout"].strip()}
    except Exception as exc:
        return {"host": host, "ok": False, "error": str(exc)}
    finally:
        client.close()

with ThreadPoolExecutor(max_workers=10) as pool:
    futures = [pool.submit(check_host, h) for h in HOSTS]
    for fut in as_completed(futures):
        print(fut.result())
```

Cap parallelism to avoid tripping `MaxSessions` on jump hosts.

---

## 6. Jump hosts (bastion)

```python
def connect_via_bastion(bastion_host, target_host, user, key_path):
    bastion = paramiko.SSHClient()
    bastion.set_missing_host_key_policy(paramiko.RejectPolicy())
    bastion.connect(bastion_host, username=user, key_filename=key_path)

    transport = bastion.get_transport()
    dest_addr = (target_host, 22)
    local_addr = ("127.0.0.1", 0)
    channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)

    target = paramiko.SSHClient()
    target.set_missing_host_key_policy(paramiko.RejectPolicy())
    target.connect(target_host, username=user, key_filename=key_path, sock=channel)
    return target
```

Same pattern as `ProxyJump` in OpenSSH config.

---

## 7. Security checklist

| Rule | Reason |
|------|--------|
| Prefer SSH keys over passwords | No secrets in scripts |
| Restrict commands | Avoid arbitrary user input in `exec_command` |
| Use sudo explicitly | `exec_command("sudo systemctl restart nginx")` |
| Log host + command, not output secrets = may contain secrets |
| Close connections in `finally` | Prevent socket leaks |

---

## 8. When to use Ansible instead

If your task is "ensure package installed" or "copy file idempotently," use Ansible modules. Use Paramiko when you need:

- Custom binary protocol over SSH tunnel
- Integration with Python data pipelines
- Conditional logic too complex for Jinja in playbooks

---

## 9. Lab — Day 18

Work from `python/day18/labs/`. Requires at least one SSH-accessible Linux host (Ansible handbook Day 1 lab VM works).

1. `pip install paramiko`.
2. Copy `inventory.yaml.example` to `inventory.yaml` with your host IP and user.
3. Run `python ssh_deploy.py ping` — runs `hostname` on all hosts.
4. Run `python ssh_deploy.py upload labs/files/motd.txt /tmp/handbook-motd.txt`.
5. Run `python ssh_deploy.py exec "cat /tmp/handbook-motd.txt"`.
6. Introduce wrong key path — confirm per-host error in JSON output.
7. Run with `--parallel 5` against 2+ hosts; compare serial vs parallel timing.

**Stretch:** Add `--sudo` flag that wraps commands with `sudo -n` and detects permission failures.

---

## 10. DevOps connections

- **Bootstrap:** Terraform creates VM → Paramiko/Python verifies SSH before Ansible first run.
- **Incident response:** Run diagnostic commands across ASG instances from a bastion script.
- **Legacy:** Not every fleet has Ansible; Paramiko scripts port to air-gapped environments easily.

---

## Quick reference

| Task | Paramiko |
|------|----------|
| Connect | `SSHClient().connect(...)` |
| Run command | `exec_command("cmd")` + `recv_exit_status()` |
| Upload file | `open_sftp().put(local, remote)` |
| Known hosts | `load_system_host_keys()` + `RejectPolicy` |
| Parallel | `ThreadPoolExecutor` per host |

**Next:** [Day 19 — Git automation with GitPython](../day19/)
