# Day 3 — Docker Compose and Multi-Container Apps

**Goal:** Define multi-service stacks declaratively, orchestrate dependencies, and run realistic local dev environments.

## Learning objectives

- Write `docker-compose.yml` / `compose.yaml` files
- Model services, networks, volumes, and environment
- Use profiles, healthchecks, and dependency ordering
- Run, scale, and debug composed stacks

---

## 1. Why Compose?

Running three containers manually:

```bash
docker network create app-net
docker run -d --name db --network app-net -e POSTGRES_PASSWORD=secret postgres:16-alpine
docker run -d --name redis --network app-net redis:7-alpine
docker run -d --name api --network app-net -p 3000:3000 -e DATABASE_URL=... myapi
```

Compose replaces this with **one file** and **one command**: `docker compose up`.

DevOps use cases:

- Local dev matching production topology
- Integration test environments in CI
- Demo/staging stacks on a single VM
- Foundation before Kubernetes (similar service concepts)

---

## 2. Compose file structure

Modern projects use `compose.yaml` (Compose Specification). Docker Compose v2 is a CLI plugin: `docker compose` (space, not hyphen).

```yaml
services:
  web:
    image: nginx:1.27-alpine
    ports:
      - "8080:80"
    depends_on:
      api:
        condition: service_healthy

  api:
    build: ./api
    environment:
      DATABASE_URL: postgres://app:secret@db:5432/appdb
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: appdb
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d appdb"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  pgdata:
```

**Key fields:**

| Field | Purpose |
|-------|---------|
| `services` | Containers to run |
| `build` / `image` | Build from Dockerfile or pull image |
| `ports` | Publish ports (`host:container`) |
| `environment` / `env_file` | Config |
| `volumes` | Named or bind mounts |
| `networks` | Custom networking (Day 4) |
| `depends_on` | Startup order (use with healthchecks) |
| `healthcheck` | When service is "ready" |
| `restart` | `unless-stopped`, `always`, `on-failure` |
| `profiles` | Optional services (`docker compose --profile debug up`) |

---

## 3. Essential commands

```bash
docker compose up              # Foreground, build if needed
docker compose up -d           # Detached
docker compose up --build      # Force rebuild
docker compose down            # Stop and remove containers
docker compose down -v         # Also remove named volumes
docker compose ps
docker compose logs
docker compose logs -f api
docker compose exec api sh
docker compose run --rm api npm test   # One-off command
docker compose config          # Validate and render merged YAML
docker compose pull
docker compose build api
docker compose up -d --scale worker=3    # Scale stateless services
```

---

## 4. Environment and secrets

**`.env` file** (auto-loaded from project directory):

```env
POSTGRES_PASSWORD=secret
APP_PORT=3000
```

Reference in compose:

```yaml
environment:
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
ports:
  - "${APP_PORT:-3000}:3000"
```

**Production note:** Do not commit real secrets. Use Docker secrets (Swarm), vault, or CI secret stores. For local dev, `.env` is fine if gitignored.

---

## 5. Override files

`compose.yaml` — shared base. `compose.override.yaml` — local dev auto-merged.

```yaml
# compose.override.yaml (gitignored or committed for dev)
services:
  api:
    volumes:
      - ./api/src:/app/src    # Hot reload
    environment:
      DEBUG: "true"
```

```bash
docker compose -f compose.yaml -f compose.prod.yaml up -d
```

---

## 6. DevOps context

- **CI:** `docker compose -f compose.test.yaml up --abort-on-container-exit --exit-code-from test`
- **Parity:** Same compose file (or rendered manifest) reduces "works on my machine"
- **Kubernetes migration:** Each `service` maps loosely to a Deployment + Service
- **Healthchecks:** Required for reliable `depends_on` and load balancer readiness

---

## Lab — Day 3

Stack files are in [`labs/full-stack/`](./labs/full-stack/).

### Part A: Start the stack

```bash
cd docker/day3/labs/full-stack
docker compose config    # Validate
docker compose up -d --build
docker compose ps
curl -s http://localhost:8080
curl -s http://localhost:8080/api/health
```

### Part B: Observe dependencies

```bash
docker compose logs db | tail -20
docker compose logs api | tail -20
docker compose exec db psql -U app -d appdb -c '\dt'
```

### Part C: Break and fix

1. Stop db: `docker compose stop db`
2. Hit `/api/health` — observe failure
3. `docker compose start db` — wait for healthy, retry

### Part D: One-off task

```bash
docker compose run --rm api node -e "console.log(process.env.DATABASE_URL)"
```

### Part E: Teardown

```bash
docker compose down
docker compose down -v   # Wipes DB volume — use when you want fresh data
```

### Challenge

Add a `redis` service and wire the API to cache `/api/health` responses for 10 seconds (sample env vars provided in compose comments).

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `service "api" depends on undefined service` | Check service names match exactly |
| Port conflict | Change host port in compose |
| DB connection refused on startup | Add healthcheck + `depends_on: condition: service_healthy` |
| Stale build | `docker compose build --no-cache api` |

---

## Day 3 checklist

- [ ] Wrote or modified a compose file
- [ ] Used `up`, `down`, `logs`, `exec`
- [ ] Understand volumes and env interpolation
- [ ] Used healthchecks for startup ordering
- [ ] Ran a one-off command with `compose run`

**Next:** [Day 4 — Networking](../day4/)
