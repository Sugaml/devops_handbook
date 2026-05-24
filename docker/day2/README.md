# Day 2 — Dockerfiles, Layers, and Image Builds

**Goal:** Write efficient Dockerfiles, understand layer caching, and build production-ready images.

## Learning objectives

- Write a Dockerfile from scratch
- Understand image layers and build cache
- Use `.dockerignore`
- Apply multi-stage builds to shrink images
- Tag and inspect built images

---

## 1. From `docker run` to `docker build`

Day 1 used pre-built images. In DevOps you **define** images as code in a `Dockerfile`:

```dockerfile
FROM base-image:tag
RUN command-that-modifies-filesystem
COPY source dest
ENV KEY=value
EXPOSE port
CMD ["executable", "arg"]
```

Build context = directory sent to the daemon (often `.`). Only include what the image needs.

---

## 2. Dockerfile instructions

| Instruction | Purpose |
|-------------|---------|
| `FROM` | Base image (required first instruction) |
| `RUN` | Execute command during build; creates a layer |
| `COPY` / `ADD` | Copy files from build context |
| `WORKDIR` | Set working directory |
| `ENV` | Environment variable at build and run time |
| `ARG` | Build-time variable (not in final env unless re-exported) |
| `EXPOSE` | Documentation of intended port (does not publish) |
| `USER` | Run as non-root (security — Day 6) |
| `CMD` | Default command when container starts (overridable) |
| `ENTRYPOINT` | Main executable (harder to override) |

**CMD vs ENTRYPOINT:**

```dockerfile
# Override entire command: docker run img echo hi
CMD ["nginx-messages", "hello"]

# Args append to entrypoint: docker run img --help
ENTRYPOINT ["nginx", "-g"]
CMD ["daemon off;"]
```

Prefer `COPY` over `ADD` unless you need tar auto-extract or remote URL (rare).

---

## 3. Layer caching

Each instruction creates a **layer**. Unchanged layers are reused from cache.

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./      # Cache busts only when deps change
RUN npm ci --omit=dev
COPY . .
RUN npm run build
CMD ["node", "dist/server.js"]
```

**Rules of thumb:**

1. Put slow, stable steps **early** (base image, dependency install).
2. Put frequently changing steps **late** (app source).
3. Combine related `RUN` commands to reduce layers: `RUN apk add --no-cache git && rm -rf /var/cache/apk/*`
4. Use `--no-cache` on `docker build` to force full rebuild when debugging.

```bash
docker build -t myapp:1.0 .
docker build --no-cache -t myapp:1.0 .
```

---

## 4. `.dockerignore`

Same idea as `.gitignore` — keeps build context small and avoids leaking secrets.

```
.git
node_modules
*.md
.env
Dockerfile*
.dockerignore
dist
coverage
```

Without it, `COPY . .` sends everything to the daemon — slow and risky.

---

## 5. Multi-stage builds

Build with full toolchain; ship minimal runtime image.

```dockerfile
# Stage 1: build
FROM golang:1.22-alpine AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /app .

# Stage 2: runtime
FROM alpine:3.20
RUN apk add --no-cache ca-certificates
COPY --from=builder /app /usr/local/bin/app
USER nobody
ENTRYPOINT ["/usr/local/bin/app"]
```

Result: image may drop from ~800 MB to ~15 MB.

---

## 6. Build commands

```bash
docker build -t myorg/myapp:1.0.0 .
docker build -t myorg/myapp:latest .
docker build -f docker/Dockerfile.prod -t myorg/myapp:prod .

docker tag myorg/myapp:1.0.0 myorg/myapp:latest
docker images myorg/myapp
docker history myorg/myapp:1.0.0
docker inspect myorg/myapp:1.0.0
```

**Build args:**

```dockerfile
ARG NODE_VERSION=20
FROM node:${NODE_VERSION}-alpine
```

```bash
docker build --build-arg NODE_VERSION=22 -t myapp .
```

---

## 7. DevOps context

- **Dockerfile lives in repo** — reviewed in PRs like application code.
- **Immutable tags** — use semver or git SHA (`myapp:abc1234`), not only `latest` in prod.
- **Base image pinning** — `node:20.11-alpine`, not `node:latest`.
- **BuildKit** (default in modern Docker): faster parallel builds, `--mount=type=cache` for dependency caches.

```bash
DOCKER_BUILDKIT=1 docker build -t myapp .
```

---

## Lab — Day 2

Use files in [`labs/`](./labs/).

### Part A: Static site

```bash
cd
cd docker/day2/labs/static-site
docker build -t handbook-static:1 .
docker run -d --name static -p 8080:80 handbook-static:1
curl -s http://localhost:8080
docker stop static && docker rm static
```

### Part B: Node API

```bash
cd docker/day2/labs/node-api
docker build -t handbook-api:1 .
docker run -d --name api -p 3000:3000 handbook-api:1
curl -s http://localhost:3000/health
docker logs api
docker stop api && docker rm api
```

### Part C: Cache experiment

1. Build `node-api` once. Note build time.
2. Change only `src/index.js` (e.g. change message).
3. Rebuild — observe `COPY` and later steps rerun; `npm ci` cached.
4. Add a line to `package.json`, rebuild — `npm ci` reruns.

### Part D: Multi-stage Go binary

```bash
cd docker/day2/labs/go-api
docker build -t handbook-go:1 .
docker images handbook-go:1   # Compare size to node-api
docker run --rm -p 8080:8080 handbook-go:1
curl -s http://localhost:8080/
```

### Challenge

Add a non-root `USER` to the Node API Dockerfile. Rebuild and verify with `docker exec api id`.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Build context huge / slow | Add `.dockerignore` |
| `npm ci` fails in build | Ensure `package-lock.json` is copied |
| Wrong architecture on Apple Silicon | Use `--platform linux/amd64` if deploying to x86 |
| Secret in image layer | Never `COPY .env`; use runtime secrets (Day 6) |

---

## Day 2 checklist

- [ ] Wrote and built from a Dockerfile
- [ ] Understand layer order and cache invalidation
- [ ] Created `.dockerignore`
- [ ] Built a multi-stage image and compared sizes
- [ ] Tagged images with meaningful names

**Next:** [Day 3 — Docker Compose](../day3/)
