# Day 1 — NGINX Basics: Install, Config Test & First Sites

**Goal:** Understand the nginx config hierarchy, run the lab stack, serve static content, and safely reload configuration.

**Time:** 3–4 hours

---

## 1. Why nginx in DevOps?

| Role | Example |
|------|---------|
| Reverse proxy | Route `/api` to app servers |
| Load balancer | Distribute traffic across upstreams |
| TLS termination | Certificates at the edge |
| Static CDN origin | Serve assets, cache headers |
| Ingress data plane | Kubernetes Ingress controllers |

---

## 2. Config hierarchy

```
nginx.conf
  └── events { worker_connections; }
  └── http {
        upstream { ... }
        server { listen; server_name; location { ... } }
      }
```

Lab configs: `labs/conf/*.conf` mounted to `/etc/nginx/conf.d/`.

---

## 3. Start the lab

```bash
cd nginx
docker compose up -d
curl -s http://localhost:8081/ | head -3
curl -s http://localhost:8082/ | head -3
curl -s http://localhost:8080/health
```

---

## 4. Essential commands

```bash
docker compose exec nginx nginx -t          # syntax test — always first
docker compose exec nginx nginx -s reload   # graceful reload
docker compose logs -f nginx
```

Inside container:

```bash
nginx -T   # dump full effective config
```

---

## 5. `location` matching (preview)

| Modifier | Match |
|----------|-------|
| `=` | Exact URI |
| `^~` | Prefix, stop search |
| `~` | Regex (case sensitive) |
| (none) | Prefix |

```nginx
location = /health { return 200 "ok\n"; }
location /static/ { alias /var/www/static/; }
```

---

## Lab

1. Start stack; verify Site A (8081) and Site B (8082).
2. Add `location /version` on port 8081 returning plain text `handbook-day1`.
3. `nginx -t` and reload; verify with `curl`.
4. Intentionally break config (missing `}`) — confirm `nginx -t` fails and reload is rejected.
5. Read `docker compose exec nginx nginx -T | head -40`.

---

## Day 1 checklist

- [ ] Understand server/location blocks
- [ ] Used `nginx -t` before reload
- [ ] Served two vhosts on different ports
- [ ] Fixed a deliberate syntax error

**Next:** [Day 2 — Upstreams & load balancing](../day2/)
