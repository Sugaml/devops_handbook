# Day 6 — Rate Limiting, Security Headers & Access Control

**Goal:** Protect origins with `limit_req`, add security headers, and restrict paths by IP or basic auth.

**Time:** 4 hours

---

## 1. Rate limiting

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    proxy_pass http://handbook_api/;
}
```

| Parameter | Meaning |
|-----------|---------|
| `rate` | Sustained requests per second |
| `burst` | Queue size for spikes |
| `nodelay` | Reject excess immediately vs queue |

Returns **503** when exceeded — tune for API contracts.

---

## 2. Security headers

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'" always;
```

Use `always` so headers appear on error responses too.

---

## 3. Access control

```nginx
location /admin/ {
    allow 10.0.0.0/8;
    deny all;
}
```

Basic auth (lab only — prefer SSO/OIDC at edge in production):

```nginx
auth_basic "Restricted";
auth_basic_user_file /etc/nginx/.htpasswd;
```

---

## Lab

1. Add `limit_req` to `/api/` — flood with `ab -n 100 -c 20` and observe 503s.
2. Add security headers to port 8081 server; verify with `curl -I`.
3. Create `/admin/` returning 403 for all except `127.0.0.1` (use `allow 127.0.0.1` in container network context).
4. List three attacks these headers mitigate (clickjacking, MIME sniffing, etc.).

---

## Day 6 checklist

- [ ] Configured limit_req zone
- [ ] Added security headers
- [ ] Used allow/deny
- [ ] Understand 503 vs 429 semantics

**Next:** [Day 7 — Operations capstone](../day7/)
