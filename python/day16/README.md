# Day 16 — Docker Automation (SDK & Subprocess Patterns)

**Goal:** Automate Docker from Python using the official Docker SDK and subprocess fallbacks — list containers, inspect health, manage images, and run one-off tasks in DevOps workflows.

**Time:** 4–5 hours (theory + hands-on)

---

## 1. When to automate Docker from Python

| Scenario | Example |
|----------|---------|
| CI test runner | Spin up Postgres, run migrations, tear down |
| Local dev orchestration | Start dependency stack before integration tests |
| Ops scripts | Prune old images, report unhealthy containers |
| Deploy helpers | Pull tagged image, recreate container with new env |

Two approaches:

```
  docker SDK (docker-py)     ──►  Docker Engine API via Unix socket
  subprocess + docker CLI    ──►  Same daemon, shell-friendly output
```

Use the **SDK** for structured data and error types. Use **subprocess** when the CLI flag you need is not exposed cleanly in the SDK.

---

## 2. Prerequisites

```bash
# Docker Desktop or Engine running
docker info

pip install docker
python3 -c "import docker; print(docker.from_env().ping())"
```

The SDK reads `DOCKER_HOST` — default `unix:///var/run/docker.sock`.

---

## 3. Docker SDK — clients and containers

```python
import docker

client = docker.from_env()

# List running containers
for c in client.containers.list():
    print(c.name, c.status, c.image.tags)

# Get one container
container = client.containers.get("my-app")
print(container.attrs["State"]["Health"]["Status"])  # if HEALTHCHECK defined
```

**Run a one-off container:**

```python
output = client.containers.run(
    "alpine:3.19",
    command=["echo", "hello"],
    remove=True,
    stdout=True,
    stderr=True,
)
print(output.decode())
```

---

## 4. Images — pull, tag, prune

```python
client = docker.from_env()

# Pull
client.images.pull("nginx", tag="1.27-alpine")

# List
for img in client.images.list(name="nginx"):
    print(img.short_id, img.tags)

# Prune unused images (careful in shared CI)
report = client.images.prune(filters={"dangling": True})
print(report.get("SpaceReclaimed", 0))
```

Always confirm `dangling` vs `all` before prune in production scripts.

---

## 5. Subprocess pattern — when CLI is simpler

```python
import subprocess
import json

def docker_inspect(container: str) -> dict:
    result = subprocess.run(
        ["docker", "inspect", container],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    return data[0]

def docker_ps_json() -> list[dict]:
    result = subprocess.run(
        ["docker", "ps", "--format", "{{json .}}"],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return [json.loads(line) for line in lines]
```

`docker ps --format '{{json .}}'` gives one JSON object per line — easy to parse without the SDK.

---

## 6. Health and exit codes

```python
def wait_healthy(client, name: str, timeout: int = 60) -> bool:
    import time
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        c = client.containers.get(name)
        health = c.attrs["State"].get("Health")
        if health and health.get("Status") == "healthy":
            return True
        if c.status == "running" and health is None:
            return True  # no HEALTHCHECK defined
        time.sleep(2)
    return False
```

Match this with Day 12 HTTP checks for apps without Docker HEALTHCHECK.

---

## 7. Compose and networks (SDK limits)

Complex multi-container stacks often stay in **docker compose**. Python can invoke:

```python
subprocess.run(
    ["docker", "compose", "-f", "docker-compose.yml", "up", "-d"],
    check=True,
)
```

Or use `client.networks.create`, `client.containers.run(..., network=...)` for programmatic setups.

---

## 8. Error handling

```python
import docker.errors

try:
    client.containers.get("missing")
except docker.errors.NotFound:
    print("Container not found")
except docker.errors.APIError as exc:
    print(f"Docker API error: {exc}")
```

Subprocess equivalent: check `returncode` and parse stderr.

---

## 9. Lab — Day 16

Work from `python/day16/labs/`. Requires Docker running.

1. `pip install docker`.
2. Run `python docker_ops.py ps` — lists running containers (JSON).
3. Run `python docker_ops.py run-alpine` — one-off echo container.
4. Start nginx: `docker run -d --name handbook-nginx -p 8080:80 nginx:1.27-alpine`
5. Run `python docker_ops.py inspect handbook-nginx` — status and ports.
6. Run `python docker_ops.py ps-subprocess` — compare SDK vs CLI output.
7. Stop and remove: `python docker_ops.py rm handbook-nginx`

**Stretch:** Script that prunes dangling images older than N days using image metadata.

---

## 10. DevOps connections

- **CI:** Most pipelines use `docker run` directly; Python wraps the same for custom test harnesses.
- **Kubernetes:** Container runtime differs (containerd); Day 17 covers cluster API — don't shell to `docker` on nodes in prod.
- **Image scanning:** Pull in Python, hand off to Trivy/Grype via subprocess.

---

## Quick reference

| Task | SDK | CLI |
|------|-----|-----|
| Ping daemon | `docker.from_env().ping()` | `docker info` |
| List containers | `client.containers.list()` | `docker ps` |
| Run one-off | `containers.run(..., remove=True)` | `docker run --rm` |
| Inspect | `container.attrs` | `docker inspect` |
| Pull image | `client.images.pull()` | `docker pull` |

**Next:** [Day 17 — Kubernetes client-python basics](../day17/)
