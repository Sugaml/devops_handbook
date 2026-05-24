# Day 1 — Containers, Images, and the Docker CLI

**Goal:** Understand what Docker is, how images and containers relate, and confidently use the core CLI commands.

## Learning objectives

- Explain containers vs virtual machines and why DevOps teams use Docker
- Install and verify Docker Engine
- Pull, run, inspect, and remove containers and images
- Use essential flags: `-d`, `-p`, `-e`, `--name`, `--rm`, `-it`
- Read container logs and exec into running containers

---

## 1. Why Docker in DevOps?

| Virtual Machine | Container |
|-----------------|-----------|
| Full OS per instance | Shares host kernel |
| GB-scale, minutes to boot | MB-scale, seconds to start |
| Hypervisor overhead | Lightweight isolation via namespaces/cgroups |

**DevOps wins:**

- **Same artifact everywhere** — build once, run on laptop, CI, staging, prod
- **Fast feedback** — spin up dependencies (DB, cache, queue) in seconds
- **Immutable infrastructure** — replace containers instead of patching servers
- **CI/CD native** — images are the deploy unit; tags are releases

Docker is not the only runtime (Podman, containerd, CRI-O exist), but its CLI and Dockerfile format are the industry lingua franca.

---

## 2. Core concepts

```
Registry (Docker Hub, ECR, GCR)
        │
        ▼ pull / push
     Image  ──► read-only template (layers + metadata)
        │
        ▼ docker run
   Container ──► running (or stopped) instance of an image
```

- **Image** — filesystem snapshot + default command. Identified by `name:tag` (e.g. `nginx:1.27-alpine`).
- **Container** — writable layer on top of an image; has ID, name, network, optional mounts.
- **Registry** — stores and distributes images. Default: [Docker Hub](https://hub.docker.com).
- **Docker Engine** — daemon (`dockerd`) + CLI (`docker`) that talk over a socket.

When you `docker run`, Docker creates a writable layer. When the container is removed, that layer is gone unless you commit it to a new image.

---

## 3. Installation and verification

### Linux (Ubuntu/Debian)

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in, then:
docker version
docker run hello-world
```

### macOS / Windows

Install [Docker Desktop](https://docs.docker.com/desktop/). It bundles Engine, CLI, and Compose.

### Verify client and server

```bash
docker version          # Client + Server sections both present
docker info | head -20  # Storage driver, cgroup, registry mirrors
```

---

## 4. Essential commands

### Images

```bash
docker search nginx              # CLI search is limited; use hub.docker.com
docker pull nginx:1.27-alpine
docker images
docker image inspect nginx:1.27-alpine
docker image rm nginx:1.27-alpine
docker image prune -a            # Remove unused images (interactive)
```

### Running containers

```bash
# Interactive shell (Alpine is tiny — good for learning)
docker run -it --rm alpine:3.20 sh

# Detached web server with port mapping
docker run -d --name web -p 8080:80 nginx:1.27-alpine

# Environment variables
docker run -d --rm --name db \
  -e POSTGRES_PASSWORD=secret \
  postgres:16-alpine

docker ps       # Running only
docker ps -a    # All containers
```

### Flag reference

| Flag | Meaning |
|------|---------|
| `-d` | Detached (background) |
| `-it` | Interactive + TTY |
| `--rm` | Auto-remove on exit |
| `--name NAME` | Human-friendly name |
| `-p HOST:CONTAINER` | Publish port |
| `-e KEY=VAL` | Environment variable |
| `-v HOST:CONTAINER` | Mount volume (Day 5) |

### Lifecycle

```bash
docker stop web
docker start web
docker restart web
docker rm web
docker rm -f web    # Force remove running container
```

### Logs and debugging

```bash
docker logs web
docker logs -f web          # Follow (like tail -f)
docker logs --tail 50 web
docker exec -it web sh      # Shell inside running container
docker top web              # Processes inside container
docker inspect web          # Full JSON metadata
docker inspect -f '{{.NetworkSettings.IPAddress}}' web
```

### Resource cleanup

```bash
docker container prune   # Stopped containers
docker system df         # Disk usage summary
docker system prune -a   # Aggressive cleanup (careful!)
```

---

## 5. How `docker run` parses arguments

Order matters less than flags, but the pattern is:

```bash
docker run [OPTIONS] IMAGE [COMMAND] [ARG...]
```

Examples:

```bash
docker run alpine:3.20 echo hello
docker run -d --name web -p 8080:80 nginx:1.27-alpine nginx -g 'daemon off;'
```

The image's `CMD`/`ENTRYPOINT` (Day 2) defines the default process; you can override at run time.

---

## 6. DevOps context

- **Local dev:** Replace "install Postgres locally" with `docker run postgres`.
- **CI pipelines:** Every job starts from a clean image — reproducible builds.
- **Kubernetes:** Nodes run containerd; you still build/push Docker/OCI images.
- **12-factor apps:** Config via `-e` / env files; stateless processes in containers.

---

## Lab — Day 1

Complete these steps in order. Use `--rm` on throwaway containers.

### Part A: First container

```bash
docker run hello-world
docker pull alpine:3.20
docker run -it --rm alpine:3.20 sh
# Inside: uname -a, cat /etc/os-release, exit
```

### Part B: Web server

```bash
docker run -d --name day1-web -p 8080:80 nginx:1.27-alpine
curl -s http://localhost:8080 | head -5
docker logs day1-web
docker exec day1-web cat /etc/nginx/nginx.conf | head -10
docker stop day1-web && docker rm day1-web
```

### Part C: Postgres quickstart

```bash
docker run -d --name day1-db \
  -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=appsecret \
  -e POSTGRES_DB=appdb \
  postgres:16-alpine

docker exec -it day1-db psql -U app -d appdb -c "SELECT version();"
docker stop day1-db && docker rm day1-db
```

### Part D: Inspect and compare

```bash
docker pull nginx:1.27-alpine
docker images nginx
docker image inspect nginx:1.27-alpine --format '{{.Os}}/{{.Architecture}} {{.Size}}'
docker history nginx:1.27-alpine
```

### Challenge

Run two nginx containers on ports **8081** and **8082** simultaneously. Verify both with `curl`. Clean up when done.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Cannot connect to the Docker daemon` | Start Docker Desktop / `sudo systemctl start docker` |
| `permission denied` on Linux | Add user to `docker` group; re-login |
| Port already in use | Change host port: `-p 8081:80` |
| Container exits immediately | Check logs: `docker logs <name>`; likely missing `-d` or wrong CMD |

---

## Day 1 checklist

- [ ] `docker version` shows client and server
- [ ] Ran interactive and detached containers
- [ ] Mapped ports and hit a service with `curl`
- [ ] Used `logs`, `exec`, and `inspect`
- [ ] Cleaned up containers and understand `prune`
- [ ] Completed the challenge (two nginx instances)

**Next:** [Day 2 — Dockerfiles and image builds](../day2/)
