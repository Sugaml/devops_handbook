# Day 7 — Logging, Metrics, Troubleshooting & Capstone

**Goal:** Use access/error logs for incidents, expose stub_status for monitoring, and deliver a production-style vhost config.

**Time:** 5–6 hours

---

## 1. Log formats

```nginx
log_format handbook '$remote_addr - $request '
                    '$status $body_bytes_sent '
                    'rt=$request_time uct=$upstream_connect_time '
                    'uht=$upstream_header_time urt=$upstream_response_time';

access_log /var/log/nginx/access.log handbook;
error_log  /var/log/nginx/error.log warn;
```

**High-signal fields for DevOps:** `$status`, `$request_time`, `$upstream_response_time`.

---

## 2. Debug upstream issues

| Symptom | Check |
|---------|-------|
| 502 Bad Gateway | upstream down, wrong port, timeout |
| 504 Gateway Timeout | `proxy_read_timeout`, app hang |
| 404 on API | `proxy_pass` path slash mismatch |
| 413 | `client_max_body_size` |

```bash
docker compose logs nginx | tail -50
docker compose exec nginx tail -20 /var/log/nginx/error.log
```

---

## 3. stub_status (metrics hook)

```nginx
location /nginx_status {
    stub_status;
    allow 127.0.0.1;
    deny all;
}
```

Pair with **nginx-prometheus-exporter** in production ([Monitoring](../monitoring/) Day 6).

---

## 4. Kubernetes Ingress (bridge)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: handbook
spec:
  ingressClassName: nginx
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web
                port:
                  number: 80
```

Controller translates to nginx config — debug with `kubectl describe ingress`.

---

## Capstone lab

Build `day7/labs/capstone.conf` (or extend `00-handbook.conf`) that includes:

1. HTTPS on 8443 (Day 4 certs)
2. Reverse proxy `/api/` with headers and timeouts (Day 3)
3. `limit_req` on `/api/` (Day 6)
4. Custom access log format with upstream timing (Day 7)
5. `/health` returning 200 without rate limit

**Verification script:**

```bash
curl -sk https://localhost:8443/health
for i in $(seq 1 5); do curl -sk https://localhost:8443/api/; done
docker compose exec nginx nginx -t
```

Deliverable: `day7/labs/capstone_notes.md` — architecture diagram in ASCII and three troubleshooting commands you would run on-call.

---

## Day 7 checklist

- [ ] Custom log format with upstream times
- [ ] Completed capstone vhost
- [ ] Linked nginx to monitoring handbook
- [ ] Wrote capstone notes

**Track complete.**
