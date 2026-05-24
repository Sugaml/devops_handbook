# NGINX for DevOps — 7-Day Handbook

A hands-on path from your first `server` block to production reverse proxies, TLS, caching, rate limiting, and troubleshooting. Labs use Docker so you can run everything on a laptop without touching production servers.

## Structure

| Day | Topic | Folder |
|-----|--------|--------|
| 1 | Install, first site, locations, `nginx -t` | [day1](./day1/) |
| 2 | Virtual hosts, upstreams, load balancing | [day2](./day2/) |
| 3 | Reverse proxy, headers, WebSocket basics | [day3](./day3/) |
| 4 | TLS termination, certs, HSTS | [day4](./day4/) |
| 5 | Caching, compression, static asset tuning | [day5](./day5/) |
| 6 | Rate limiting, security headers, access control | [day6](./day6/) |
| 7 | Logging, monitoring hooks, K8s Ingress, capstone | [day7](./day7/) |

## Prerequisites

- Linux CLI ([Linux](../linux/README.md) Day 1–3).
- HTTP and ports ([Network](../network/README.md) Day 3 and 6).
- Docker ([Docker](../docker/README.md) Day 1–2).

## Lab environment

```bash
cd nginx
docker compose up -d
# Site A → http://localhost:8081
# Site B → http://localhost:8082
# API upstream demo → http://localhost:8080
```

Configs live under `labs/conf/` and mount into the `nginx` service.

## How to use this handbook

1. Edit configs in `labs/conf/` — never test syntax only in production.
2. After every change: `docker compose exec nginx nginx -t` then `nginx -s reload`.
3. Complete each day's **Lab** before advancing.
4. On Day 7, build a single vhost that combines proxy + TLS + rate limit (lab certs).

## Design notes

- Examples target **nginx 1.27** stable syntax.
- TLS labs use **self-signed** certificates — browsers will warn; that is expected.
- Production callouts reference Kubernetes Ingress and CDN patterns without duplicating the [Kubernetes](../kubernetes/) handbook.

## Progress checklist

```
[ ] Day 1  [ ] Day 4
[ ] Day 2  [ ] Day 5
[ ] Day 3  [ ] Day 6
[ ] Day 7 — capstone
```

## Related handbooks

| Handbook | Connection |
|----------|------------|
| [Docker](../docker/README.md) | Official nginx image, compose networking |
| [Kubernetes](../kubernetes/README.md) | Ingress controllers (nginx, traefik) |
| [Monitoring](../monitoring/README.md) | stub_status, access log metrics |
| [Network](../network/README.md) | TLS, proxies, load balancing theory |
