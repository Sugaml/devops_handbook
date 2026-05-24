# Linux for DevOps — 7-Day Handbook

A practical, CLI-first path from Linux fundamentals to production-ready DevOps workflows. Each day builds on the previous one with commands you can run on any modern distro (Ubuntu/Debian, RHEL/Rocky, Amazon Linux).

## Structure

| Day | Topic | Folder |
|-----|--------|--------|
| 1 | Filesystem, navigation, permissions | [day1](./day1/) |
| 2 | Shell, pipes, text processing | [day2](./day2/) |
| 3 | Processes, systemd, scheduling | [day3](./day3/) |
| 4 | Packages and software lifecycle | [day4](./day4/) |
| 5 | Networking, SSH, security basics | [day5](./day5/) |
| 6 | Storage, LVM, backups | [day6](./day6/) |
| 7 | Scripting, automation, troubleshooting | [day7](./day7/) |

## How to use this handbook

1. Use a lab VM or container (`docker run -it ubuntu:24.04 bash`).
2. Run every command yourself; break things in a sandbox, not production.
3. Complete each day's **Lab** section before moving on.
4. Keep a personal cheat sheet of flags you actually use.

## Recommended lab setup

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y vim curl wget git htop tree jq

# RHEL/Rocky/Amazon Linux
sudo dnf install -y vim curl wget git htop tree jq
```

## Design notes

- Commands are shown with typical flags; use `man <command>` or `tldr <command>` for full options.
- Examples use `$USER`, `/tmp`, and placeholder hosts — replace with your environment.
- DevOps context is called out where Linux skills map directly to CI/CD, Kubernetes nodes, or cloud VMs.
