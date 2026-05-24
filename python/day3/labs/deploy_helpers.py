#!/usr/bin/env python3
"""Small deploy helper functions — Day 3 lab."""

DEFAULT_ENV = "staging"


def format_banner(app: str, version: str, environment: str | None = None) -> str:
    """Return a single-line release banner."""
    env = environment or DEFAULT_ENV
    return f"[{env}] {app}@{version}"


def build_ssh_command(host: str, *extra_args: str, user: str = "deploy") -> list[str]:
    """Build argv for non-interactive SSH (no shell)."""
    cmd = ["ssh", f"{user}@{host}"]
    cmd.extend(extra_args)
    return cmd


def log_step(step: str, **context: str) -> None:
    """Print a structured step line."""
    pairs = " ".join(f"{k}={v}" for k, v in sorted(context.items()))
    print(f"STEP {step} {pairs}".strip())


def deploy_plan(app: str, hosts: list[str], **options: str) -> None:
    """Print a dry-run style plan across a fleet."""
    dry = options.get("dry_run", "true").lower() == "true"
    mode = "DRY-RUN" if dry else "APPLY"
    log_step("start", app=app, mode=mode)
    for i, host in enumerate(hosts, start=1):
        log_step("target", wave=str(i), host=host)
    log_step("done", app=app)


def main() -> None:
    print(format_banner("api", "1.2.0"))
    print(build_ssh_command("10.0.0.5", "-o", "BatchMode=yes"))
    deploy_plan("api", ["web1", "web2"], dry_run="true")


if __name__ == "__main__":
    main()
