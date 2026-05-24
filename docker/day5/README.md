# Day 5 — Volumes, Bind Mounts, and Data Persistence

**Goal:** Persist container data correctly, choose the right mount type, and apply backup/restore patterns for stateful services.

## Learning objectives

- Distinguish bind mounts, named volumes, and tmpfs
- Manage volumes with CLI and Compose
- Run stateful services (Postgres, Redis) with durable storage
- Backup, restore, and avoid common data-loss traps

---

## 1. Why persistence matters

Container filesystems are **ephemeral** by default. Remove the container → lose writes unless data lives on a mount or volume.

| Type | Stored on | Best for |
|------|-----------|----------|
| **Named volume** | Docker-managed (`/var/lib/docker/volumes/`) | DB data, shared between containers |
| **Bind mount** | Host path you specify | Dev hot-reload, config files |
| **tmpfs** | RAM | Secrets, temp cache (not durable) |

---

## 2. Named volumes

```bash
docker volume create pgdata
docker volume ls
docker volume inspect pgdata

docker run -d --name db \
  -v pgdata:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=secret \
  postgres:16-alpine

# Remove container — data survives
docker rm -f db
docker run -d --name db2 -v pgdata:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=secret postgres:16-alpine
```

Compose:

```yaml
services:
  db:
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
```

---

## 3. Bind mounts

```bash
# Host directory mounted into container
docker run -d -v $(pwd)/html:/usr/share/nginx/html:ro nginx:1.27-alpine

# Compose — relative path
volumes:
  - ./config/nginx.conf:/etc/nginx/nginx.conf:ro
  - ./src:/app/src
```

**`:ro`** = read-only (good for config). **`:rw`** = default read-write.

**DevOps caution:** Bind mounts tie container to host layout — fine for dev, often wrong for prod (use volumes or external storage).

---

## 4. tmpfs mounts

```bash
docker run --tmpfs /run/secrets:rw,noexec,nosuid,size=64m myapp
```

No data on disk — gone when container stops. Use for sensitive temp data.

---

## 5. Volume lifecycle and cleanup

```bash
docker volume ls
docker volume rm pgdata
docker volume prune          # Unused volumes only

docker compose down -v       # Removes compose-defined named volumes
```

**Data loss trap:** `docker compose down -v` in prod destroys databases. Use explicit backup procedures first.

---

## 6. Backup and restore

### Postgres example

```bash
# Backup
docker exec db pg_dump -U app appdb > backup.sql

# Or via volume snapshot (cloud/host level) — preferred at scale

# Restore
cat backup.sql | docker exec -i db psql -U app -d appdb
```

### Copy from volume

```bash
docker run --rm \
  -v pgdata:/data \
  -v $(pwd):/backup \
  alpine:3.20 tar czf /backup/pgdata.tar.gz -C /data .
```

---

## 7. Permissions and ownership

Containers often run as root; files on bind mounts may become root-owned on the host.

Fix patterns:

- Run container as host UID: `user: "${UID}:${GID}"` in compose
- `chown` in entrypoint script (dev only)
- Use named volumes (Docker handles permissions more predictably)

---

## 8. DevOps context

- **Kubernetes:** PersistentVolumeClaim ≈ named volume
- **Cloud:** EBS, Azure Disk, GCE PD attach to nodes; bind at pod level
- **Immutable app containers:** Only `/tmp` and mounted volumes are writable
- **12-factor:** Treat backing services as attached resources; config via env

---

## Lab — Day 5

Use [`labs/postgres-persist/`](./labs/postgres-persist/).

### Part A: Named volume persistence

```bash
cd docker/day5/labs/postgres-persist
docker compose up -d
docker compose exec db psql -U app -d appdb -c \
  "CREATE TABLE IF NOT EXISTS notes (id serial PRIMARY KEY, body text);"
docker compose exec db psql -U app -d appdb -c \
  "INSERT INTO notes (body) VALUES ('survives restart');"
docker compose restart db
docker compose exec db psql -U app -d appdb -c "SELECT * FROM notes;"
```

### Part B: Prove data survives container delete

```bash
docker compose down          # WITHOUT -v
docker compose up -d
docker compose exec db psql -U app -d appdb -c "SELECT * FROM notes;"
```

### Part C: Bind mount for init scripts

Inspect `init/` — SQL runs on first DB init only when volume is empty.

```bash
docker compose down -v       # Fresh volume
docker compose up -d
docker compose exec db psql -U app -d appdb -c "SELECT * FROM seed_data;"
```

### Part D: Backup and restore

```bash
docker compose exec db pg_dump -U app appdb > /tmp/appdb-backup.sql
docker compose down -v
docker compose up -d
sleep 5
cat /tmp/appdb-backup.sql | docker compose exec -T db psql -U app -d appdb
docker compose exec db psql -U app -d appdb -c "SELECT * FROM notes;"
```

### Part E: Inspect volume

```bash
docker volume ls | grep postgres
docker volume inspect postgres-persist_pgdata
```

### Challenge

Add a Redis service with a named volume for AOF persistence. Write a key, restart Redis, verify key exists.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Empty DB after restart | Was volume mounted? Used `down -v`? |
| Permission denied on bind mount | Check UID/GID and `:ro` vs `:rw` |
| Init script didn't run | Init only on empty data dir; need fresh volume |
| Disk full | `docker system df -v`; prune unused volumes carefully |

---

## Day 5 checklist

- [ ] Used named volume for database data
- [ ] Used bind mount for config or init scripts
- [ ] Performed backup and restore
- [ ] Understand `compose down` vs `compose down -v`
- [ ] Inspected volume location with `docker volume inspect`

**Next:** [Day 6 — Security and hardening](../day6/)
