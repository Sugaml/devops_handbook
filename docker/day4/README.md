# Day 4 — Docker Networking

**Goal:** Control how containers communicate — bridge networks, DNS, port publishing, and isolation patterns used in production.

## Learning objectives

- Explain default bridge vs user-defined bridge networks
- Use container DNS for service discovery
- Publish ports safely (`-p` vs `-P`)
- Connect containers across networks and debug connectivity

---

## 1. Networking model

Each container gets:

- **Network namespace** — own interfaces and routing table
- **IP address** on attached network(s)
- **DNS name** on user-defined networks (container name / service name)

Docker networks are managed by libnetwork. Common drivers:

| Driver | Use case |
|--------|----------|
| `bridge` | Single-host container communication (default) |
| `host` | Container shares host network stack (no isolation) |
| `overlay` | Multi-host (Swarm, Day 7) |
| `none` | No networking |

---

## 2. Default bridge vs user-defined bridge

**Default bridge (`docker0`):**

- Containers on default bridge communicate by IP only
- Legacy `--link` (avoid)

**User-defined bridge (recommended):**

```bash
docker network create app-net
docker run -d --name web --network app-net nginx:1.27-alpine
docker run -d --name api --network app-net myapi:latest

# From api container:
# ping web   — resolves via embedded DNS
# curl http://web
```

Compose creates a project-scoped network automatically; service names are DNS entries.

---

## 3. Inspecting networks

```bash
docker network ls
docker network inspect app-net
docker network inspect bridge

# Connect running container to another network
docker network connect app-net existing-container
docker network disconnect app-net existing-container

docker network rm app-net
docker network prune
```

---

## 4. Port publishing

```bash
# Map host 8080 to container 80
docker run -d -p 8080:80 nginx:1.27-alpine

# Bind specific interface
docker run -d -p 127.0.0.1:8080:80 nginx:1.27-alpine

# Publish all EXPOSE'd ports to random host ports
docker run -d -P nginx:1.27-alpine
docker port <container>
```

**Important:** `-p` exposes to the outside world. In production, put a reverse proxy or load balancer in front; avoid binding `0.0.0.0` for admin interfaces.

**Container-to-container** traffic on the same user-defined network uses **internal ports** — no `-p` required:

```bash
curl http://api:3000    # from another container on same network
```

---

## 5. DNS and aliases

```bash
docker run -d --name db --network app-net \
  --network-alias database postgres:16-alpine
```

Compose equivalent:

```yaml
services:
  db:
    networks:
      backend:
        aliases:
          - database
networks:
  backend:
```

Embedded DNS server (127.0.0.11) resolves service names within the network.

---

## 6. Multi-network isolation

```yaml
services:
  frontend:
    networks: [public]
  api:
    networks: [public, backend]
  db:
    networks: [backend]    # Not reachable from public-only containers

networks:
  public:
  backend:
    internal: true         # No external routing — DB subnet pattern
```

`internal: true` blocks outbound internet — useful for data layers (with careful design for updates).

---

## 7. Debugging connectivity

```bash
# Install tools in alpine for debugging
docker run -it --rm --network app-net nicolaka/netshoot

# Inside netshoot:
dig api
curl -v http://api:3000/health
nc -zv db 5432
traceroute web

# From host
docker exec api ping -c 2 db
docker exec api cat /etc/resolv.conf
```

**Common issues:**

- Wrong network — container not attached
- Wrong port — using host-mapped port inside network (use container port)
- Firewall on host blocking published ports
- App listening on `127.0.0.1` inside container (must listen `0.0.0.0`)

---

## 8. DevOps context

- **Kubernetes:** Each Pod gets an IP; Services provide DNS — same mental model as Compose networks
- **Security:** Segment networks (frontend / backend / data)
- **Service mesh** (Istio, Linkerd) adds mTLS on top of container networking
- **CI:** Ephemeral networks per job prevent cross-job leakage

---

## Lab — Day 4

Use [`labs/network-lab/`](./labs/network-lab/).

### Part A: Create isolated network

```bash
cd docker/day4/labs/network-lab
docker compose up -d
docker network ls | grep network-lab
```

### Part B: DNS resolution

```bash
docker compose exec frontend ping -c 2 backend
docker compose exec frontend wget -qO- http://backend
```

### Part C: Isolation test

```bash
# db is on internal network only — frontend should NOT reach it directly
docker compose exec frontend wget -qO- --timeout=2 http://db:5432 || echo "expected fail"
docker compose exec backend nc -zv db 5432
```

### Part D: Manual network ops

```bash
docker network create manual-net
docker run -d --name rogue --network manual-net alpine:3.20 sleep 3600
docker network connect network-lab_backend rogue
docker exec rogue ping -c 1 backend
docker network disconnect network-lab_backend rogue
docker rm -f rogue && docker network rm manual-net
```

### Part E: Port binding

```bash
curl -s http://127.0.0.1:9080
docker compose port frontend 80
```

### Challenge

Add an `admin` service on `backend` network only with a simple HTTP health endpoint. Confirm it is reachable from `backend` but not from `frontend`.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Name not resolving | Same user-defined network? Use service name not `localhost` |
| Connection refused | App must bind `0.0.0.0`; check `EXPOSE` vs actual listen port |
| Works on host, not container | Use container IP/DNS, not `host.docker.internal` unless configured |

---

## Day 4 checklist

- [ ] Created user-defined bridge network
- [ ] Used DNS names between containers
- [ ] Understand `-p` vs internal ports
- [ ] Tested network isolation with multi-network compose
- [ ] Debugged with netshoot or equivalent

**Next:** [Day 5 — Volumes and persistence](../day5/)
