# Day 7 — Registries, CI/CD, Swarm, and Troubleshooting

**Goal:** Push images to registries, integrate Docker into CI/CD, deploy a small Swarm stack, and systematically debug production container issues.

## Learning objectives

- Tag, push, and pull from Docker Hub and cloud registries
- Wire Docker build/push into a CI pipeline
- Deploy services with Docker Swarm basics
- Troubleshoot containers like a production engineer
- Apply a production readiness checklist

---

## 1. Image tagging strategy

| Tag | Use |
|-----|-----|
| `1.4.2` | Semver release |
| `1.4.2-abc1234` | Release + git SHA |
| `abc1234` | Git SHA only (immutable) |
| `main-20250524` | Branch + date |
| `latest` | Dev convenience only — avoid sole prod tag |

```bash
docker tag myapp:1.0.0 myorg/myapp:1.0.0
docker tag myapp:1.0.0 myorg/myapp:1.0
docker tag myapp:1.0.0 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:1.0.0
```

**Immutable rule:** Never overwrite a tag that already deployed to production.

---

## 2. Docker Hub and private registries

### Docker Hub

```bash
docker login
docker push myorg/myapp:1.0.0
docker pull myorg/myapp:1.0.0
```

### AWS ECR

```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-east-1.amazonaws.com

docker tag myapp:1.0.0 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:1.0.0
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:1.0.0
```

### GCP Artifact Registry / Azure ACR

Same pattern: authenticate → tag with registry URL → push.

### Self-hosted (Harbor)

Common in enterprises — vulnerability scanning, replication, RBAC.

---

## 3. CI/CD pipeline pattern

Typical flow:

```
git push → CI build → test → scan → push image → deploy
```

Example GitHub Actions (see [`labs/ci/github-actions-docker.yaml`](./labs/ci/github-actions-docker.yaml)):

```yaml
name: Build and Push
on:
  push:
    branches: [main]
jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USER }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - uses: docker/build-push-action@v6
        with:
          push: true
          tags: myorg/myapp:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

**DevOps tips:**

- Use BuildKit cache in CI (gha, registry cache)
- Multi-arch: `platforms: linux/amd64,linux/arm64`
- Sign images with Cosign after push
- Deploy by updating tag/digest in compose, Swarm, or K8s manifest

---

## 4. Docker Swarm (production-lite orchestration)

Swarm = built-in clustering. Kubernetes is the default at scale; Swarm is simpler for small fleets.

```bash
# Manager node
docker swarm init

# Worker (run token from init output)
docker swarm join --token SWMTKN-1-... manager-ip:2377

docker node ls
```

**Stack deploy** (Compose v3 with deploy keys):

```yaml
# compose.swarm.yaml
services:
  api:
    image: myorg/myapp:1.0.0
    ports:
      - "3000:3000"
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    networks:
      - webnet
networks:
  webnet:
    driver: overlay
```

```bash
docker stack deploy -c compose.swarm.yaml mystack
docker service ls
docker service ps mystack_api
docker service logs mystack_api
docker service scale mystack_api=5
docker stack rm mystack
```

**Swarm vs Kubernetes:**

| Swarm | Kubernetes |
|-------|------------|
| Built into Docker | Separate control plane |
| Simpler | Rich ecosystem |
| Overlay networking built-in | CNI plugins |
| Good_minimal | Deployments, HPA, operators |

Many Docker skills transfer directly to K8s (images, healthchecks, env, secrets).

---

## 5. Production troubleshooting playbook

### Container won't start

```bash
docker logs <container> --tail 100
docker inspect <container> --format '{{.State.ExitCode}} {{.State.Error}}'
docker events --since 10m --filter container=<name>
```

### Crash loop

```bash
docker inspect -f '{{json .State.Health}}' <container> | jq
docker run --rm -it --entrypoint sh myapp:tag   # Override CMD, debug manually
```

### Network issues

```bash
docker exec <c1> getent hosts <c2>
docker network inspect <network>
# See Day 4
```

### Disk pressure

```bash
docker system df -v
docker container prune
docker image prune -a
journalctl -u docker   # Linux daemon logs
```

### Performance

```bash
docker stats
docker exec <container> top
# Check memory limit vs OOMKilled in inspect
```

### OOMKilled

```bash
docker inspect <container> --format '{{.State.OOMKilled}}'
# Increase --memory or fix leak
```

---

## 6. Production readiness checklist

**Image**

- [ ] Pinned base image version or digest
- [ ] Non-root user
- [ ] Multi-stage build; minimal final size
- [ ] HEALTHCHECK defined
- [ ] No secrets in layers
- [ ] CI vulnerability scan gate

**Runtime**

- [ ] Resource limits set
- [ ] Restart policy configured
- [ ] Logs to stdout/stderr (JSON driver or log shipper)
- [ ] Read-only root FS where possible
- [ ] Named volumes for stateful data with backup plan

**Deploy**

- [ ] Immutable tags per release
- [ ] Rollback procedure documented
- [ ] Config via env/secrets, not image rebuild
- [ ] Monitoring and alerting on health endpoint

**Host**

- [ ] Docker daemon secured (TLS, no open TCP socket)
- [ ] Regular host and image updates
- [ ] AppArmor/SELinux where applicable

---

## Lab — Day 7

### Part A: Tag and push (Docker Hub)

```bash
cd docker/day7/labs/push-demo
docker build -t YOUR_USER/handbook-demo:day7 .
docker login
docker push YOUR_USER/handbook-demo:day7
docker rmi YOUR_USER/handbook-demo:day7
docker pull YOUR_USER/handbook-demo:day7
docker run --rm YOUR_USER/handbook-demo:day7
```

Replace `YOUR_USER` with your Docker Hub username.

### Part B: Local registry (no cloud account needed)

```bash
docker run -d -p 5000:5000 --name registry --restart=always registry:2
docker tag handbook-demo:local localhost:5000/handbook-demo:day7
docker push localhost:5000/handbook-demo:day7
docker pull localhost:5000/handbook-demo:day7
```

On Docker Desktop, you may need `insecure-registries` for localhost:5000.

### Part C: Swarm stack (single-node lab)

```bash
cd docker/day7/labs/swarm-stack
docker swarm init 2>/dev/null || true
docker build -t handbook-web:swarm .
docker stack deploy -c compose.swarm.yaml demo
docker service ls
curl -s http://localhost:8080
docker service scale demo_web=3
docker service ps demo_web
docker stack rm demo
```

### Part D: Break/fix exercise

```bash
docker run -d --name broken -p 9999:80 nginx:1.27-alpine
docker stop broken
docker update --restart unless-stopped broken
docker start broken
docker kill broken   # Simulate crash
sleep 3 && docker ps | grep broken
docker rm -f broken
```

### Part E: CI file review

Open [`labs/ci/github-actions-docker.yaml`](./labs/ci/github-actions-docker.yaml). Identify: build, cache, login, push, and where you'd add Trivy scan from Day 6.

### Challenge

Deploy the Day 3 full-stack compose as a Swarm stack (convert `build` to pre-built image). Scale API to 2 replicas. Verify both serve traffic through the web proxy.

---

## 7-Day capstone (optional)

Combine everything:

1. Build hardened API image (Day 6)
2. Compose stack with DB + Redis (Days 3–5)
3. Scan and push to registry (Day 6–7)
4. Deploy on Swarm with replicas and rolling update
5. Simulate failure; use troubleshooting playbook

Document: image tag, deploy command, rollback command, backup command.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `denied: requested access` on push | `docker login`; check repo name matches user/org |
| Swarm service pending | Image not on all nodes — use registry, not local-only tag |
| `no suitable node` | Constraints/placement; check `docker node ls` |
| Registry cert error | Use HTTPS or configure insecure registry (dev only) |

---

## Day 7 checklist

- [ ] Pushed image to a registry
- [ ] Understand tagging and immutability
- [ ] Deployed a Swarm stack and scaled a service
- [ ] Walked through troubleshooting playbook
- [ ] Reviewed CI pipeline YAML
- [ ] Completed production readiness checklist review

**Congratulations** — you've completed the 7-day Docker for DevOps handbook. Revisit weak areas, then explore Kubernetes (Deployments, Services, Ingress) using the same images you built here.
