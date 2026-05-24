# Day 6 — Security, Scanning, and Production Hardening

**Goal:** Build and run containers that meet production security expectations — least privilege, minimal attack surface, and automated vulnerability checks.

## Learning objectives

- Apply Dockerfile security best practices
- Run containers as non-root with read-only root filesystem
- Set resource limits and healthchecks
- Scan images for CVEs
- Understand secrets handling and supply chain basics

---

## 1. Security mindset for containers

Containers are **not VMs**. They share the kernel. A container escape or root compromise can affect the host.

**Defense layers:**

1. Minimal base image (Alpine, distroless, scratch)
2. Non-root user
3. Read-only root filesystem + tmpfs for writable paths
4. No secrets in image layers
5. Resource limits (CPU, memory, PIDs)
6. Image scanning in CI
7. Pin base image digests

---

## 2. Dockerfile hardening

```dockerfile
FROM node:20-alpine AS base
WORKDIR /app

# Run as non-root
RUN addgroup -g 1001 app && adduser -u 1001 -G app -D app

COPY --chown=app:app package*.json ./
RUN npm ci --omit=dev && npm cache clean --force

COPY --chown=app:app . .
USER app

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1:3000/health || exit 1

CMD ["node", "src/index.js"]
```

**Checklist:**

- Pin versions: `node:20.11-alpine`, not `latest`
- Combine `RUN` and clean caches in same layer
- Use `--chown` on COPY when dropping root
- Avoid `curl | bash` in production images
- Multi-stage: no compiler/toolchain in final image

---

## 3. Runtime hardening

```bash
docker run -d \
  --name hardened-api \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --user 1001:1001 \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --memory 256m \
  --cpus 0.5 \
  --pids-limit 100 \
  -p 3000:3000 \
  myapi:1.0
```

| Flag | Purpose |
|------|---------|
| `--read-only` | Root FS immutable |
| `--tmpfs` | Writable temp paths |
| `--cap-drop ALL` | Drop Linux capabilities |
| `--security-opt no-new-privileges` | Block privilege escalation |
| `--memory` / `--cpus` | Prevent resource exhaustion |
| `--pids-limit` | Limit fork bombs |

Compose equivalent:

```yaml
services:
  api:
    read_only: true
    tmpfs:
      - /tmp
    user: "1001:1001"
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 256M
        reservations:
          memory: 128M
```

---

## 4. Secrets — never bake them in

**Bad:**

```dockerfile
ENV API_KEY=sk-live-xxxxx
COPY .env .
```

**Good:**

```bash
docker run -e API_KEY \
  --env-file .env.production \   # gitignored, injected at deploy
  myapp
```

**Better (orchestrators):** Docker Swarm secrets, Kubernetes Secrets + external vault (HashiCorp Vault, AWS Secrets Manager).

Secrets in env vars are visible in `docker inspect`. For high sensitivity, use runtime secret mounts (Swarm/K8s) or init containers.

---

## 5. Image scanning

```bash
# Docker Scout (built into Docker Desktop / CLI plugin)
docker scout quickview myapp:1.0
docker scout cves myapp:1.0

# Trivy (popular OSS scanner)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image myapp:1.0

# Fail CI on critical CVEs
trivy image --exit-code 1 --severity CRITICAL myapp:1.0
```

**CI pattern:**

```yaml
# GitHub Actions excerpt
- name: Build
  run: docker build -t myapp:${{ github.sha }} .
- name: Scan
  run: trivy image --exit-code 1 --severity HIGH,CRITICAL myapp:${{ github.sha }}
```

Fix: rebuild when base image patches release; enable Dependabot/Renovate for dependency updates.

---

## 6. Supply chain

- Pull from trusted registries only
- Pin by **digest**: `nginx@sha256:abc123...`
- Sign images (Docker Content Trust, Cosign/Sigstore)
- Verify SBOMs for compliance
- Use official or org-maintained base images

```bash
docker pull nginx@sha256:<digest>
docker trust inspect nginx:latest   # if DCT enabled
```

---

## 7. Rootless Docker (awareness)

Rootless mode runs daemon and containers without root on host — reduces host compromise blast radius. Setup varies by distro; see [Docker docs](https://docs.docker.com/engine/security/rootless/).

---

## 8. DevOps context

- **Policy as code:** OPA/Gatekeeper, Kyverno (K8s) enforce non-root, no `:latest`
- **CIS Docker Benchmark:** Hardening checklist for hosts and daemon
- **Pod Security Standards:** K8s equivalent of cap-drop + non-root
- **Shift left:** Scan in CI before push to registry

---

## Lab — Day 6

Use [`labs/hardened-api/`](./labs/hardened-api/).

### Part A: Compare images

```bash
cd docker/day6/labs/hardened-api
docker build -f Dockerfile.insecure -t api:insecure .
docker build -f Dockerfile.secure -t api:secure .
docker images api:insecure api:secure
docker history api:insecure | head -10
docker history api:secure | head -10
```

### Part B: Run as non-root

```bash
docker run -d --name secure -p 3000:3000 api:secure
docker exec secure id
docker exec secure touch /app/test 2>&1 || echo "expected: read-only or permission denied"
curl -s http://localhost:3000/health
```

### Part C: Read-only + limits

```bash
docker rm -f secure
docker run -d --name secure \
  --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  --memory 128m --cpus 0.25 \
  -p 3000:3000 api:secure
curl -s http://localhost:3000/health
```

### Part D: Scan

```bash
docker scout quickview api:secure 2>/dev/null || \
  docker run --rm aquasec/trivy image api:secure
```

### Part E: Fix a finding

Update base image tag in `Dockerfile.secure`, rebuild, rescan. Note CVE count change.

### Challenge

Add a Compose file that runs `api:secure` with `read_only`, `cap_drop`, healthcheck, and resource limits. Verify unhealthy container restarts when health fails.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Permission denied at runtime | Ensure files owned by non-root UID in image |
| App fails with `--read-only` | Add tmpfs for dirs app writes to (`/tmp`, `/var/run`) |
| Healthcheck always failing | Use `127.0.0.1` not `localhost`; check start-period |
| Scan shows base image CVEs | Rebuild on patched base; consider distroless |

---

## Day 6 checklist

- [ ] Built non-root image with pinned base
- [ ] Ran with `--read-only` and resource limits
- [ ] Scanned image for CVEs
- [ ] Understand why secrets must not be in Dockerfile
- [ ] Know CI scan gate pattern

**Next:** [Day 7 — Registries, CI/CD, Swarm, troubleshooting](../day7/)
