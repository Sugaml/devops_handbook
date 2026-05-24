# Day 8 — argparse CLI Design for Ops Scripts

**Goal:** Build operator-friendly CLIs with subcommands, sensible defaults, `--dry-run`, and exit codes suitable for cron and CI.

**Time:** 4–5 hours

---

## 1. Why argparse for DevOps tools

| Approach | Pros | Cons |
|----------|------|------|
| `sys.argv` manual | Tiny scripts | No help, easy bugs |
| **argparse** | Stdlib, subcommands, `--help` | Verbose boilerplate |
| `click` / `typer` | Ergonomic | Extra dependency |

Start with **argparse** in pipelines where dependencies are tightly controlled.

---

## 2. Minimal parser

```python
import argparse

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="host-check",
        description="Check SSH reachability for inventory hosts",
    )
    parser.add_argument("hosts", nargs="+", help="Hostnames or IPs")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    print(args.hosts, args.timeout, args.verbose)

if __name__ == "__main__":
    main()
```

```bash
python3 host_check.py web1 web2 --timeout 2 -v
python3 host_check.py --help
```

---

## 3. Choices, types, and validation

```python
parser.add_argument(
    "--env",
    choices=["dev", "staging", "prod"],
    default="staging",
)
parser.add_argument("--port", type=int, default=22)

def positive_int(value: str) -> int:
    n = int(value)
    if n <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return n

parser.add_argument("--workers", type=positive_int, default=4)
```

---

## 4. Boolean flags

```python
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Print actions without executing",
)
parser.add_argument(
    "--no-color",
    action="store_false",
    dest="color",
    help="Disable ANSI colors",
)
parser.set_defaults(color=True)
```

---

## 5. Subcommands (deploy, rollback, status)

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fleetctl")
    sub = parser.add_subparsers(dest="command", required=True)

    deploy = sub.add_parser("deploy", help="Roll out a version")
    deploy.add_argument("--app", required=True)
    deploy.add_argument("--version", required=True)
    deploy.add_argument("--dry-run", action="store_true")

    status = sub.add_parser("status", help="Show fleet health")
    status.add_argument("--app", required=True)
    return parser
```

```bash
python3 fleetctl.py deploy --app api --version 1.2.0 --dry-run
python3 fleetctl.py status --app api
```

---

## 6. Mutually exclusive groups

```python
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--file", type=argparse.FileType("r"))
group.add_argument("--hosts", nargs="+")
```

---

## 7. Exit codes and errors

Convention for automation:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General failure |
| 2 | Misuse (argparse uses this on bad args) |

```python
import sys

def main() -> None:
    args = parser.parse_args()
    if not run(args):
        sys.exit(1)
```

Use `parser.error("message")` for user-facing validation failures (exits 2).

---

## 8. Epilog and examples in help

```python
parser = argparse.ArgumentParser(
    epilog="Example: host-check --env prod web1 web2",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
```

---

## 9. Lab — Day 8

Work from `python/day8/labs/`.

1. Run `host_check.py --help` and `host_check.py 127.0.0.1 --dry-run`.
2. Add `--env` with choices; reject unknown env.
3. Add subcommand `list-regions` that prints static region names.
4. Wire `--verbose` to increase logging level (Day 6).
5. Return exit code 1 if any host fails check (simulate with `--fail-host`).
6. Document examples in epilog; screenshot or paste help output in notes.

**Stretch:** Read hosts from `--file` OR positional hosts (mutually exclusive).

---

## 10. DevOps connections

- **Cron/Kubernetes Jobs:** Non-zero exit triggers alerts; stdout/stderr captured.
- **Makefile targets:** `deploy: ; python3 tools/deploy.py --env prod`
- **Consistency:** Match flag names with Terraform/Ansible vars (`--env`, `--region`).

---

## Quick reference

| Task | argparse |
|------|----------|
| Positional | `add_argument("name")` |
| Optional | `add_argument("--flag")` |
| List | `nargs="+"` |
| Subcommand | `add_subparsers()` |
| Parse | `args = parser.parse_args()` |
| Fail | `parser.error("msg")` |

**Next:** [Day 9 — subprocess & shell commands](../day9/)
