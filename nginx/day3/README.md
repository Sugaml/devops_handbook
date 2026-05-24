# Day 3 — Reverse Proxy, Headers & Timeouts

**Goal:** Proxy HTTP apps correctly, preserve client IP and scheme, and avoid the trailing-slash URI trap.

**Time:** 4 hours

---

## 1. `proxy_pass` URI rules

```nginx
location /api/ {
    proxy_pass http://handbook_api/;   # strips /api/ prefix
}
# Request: GET /api/foo  →  upstream GET /foo

location /api/ {
    proxy_pass http://handbook_api;    # keeps /api/ prefix
}
# Request: GET /api/foo  →  upstream GET /api/foo
```

**DevOps rule:** Match trailing slashes deliberately — mismatches cause 404 storms after deploy.

---

## 2. Essential headers

```nginx
proxy_set_header Host              $host;
proxy_set_header X-Real-IP         $remote_addr;
proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

Apps behind TLS-terminating nginx use `X-Forwarded-Proto` for redirect URLs.

---

## 3. Timeouts

```nginx
proxy_connect_timeout 5s;
proxy_send_timeout    60s;
proxy_read_timeout    60s;
```

Align with app and load balancer idle timeouts — **502** often means read timeout.

---

## 4. WebSocket upgrade (pattern)

```nginx
location /ws/ {
    proxy_pass http://app:3000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

---

## Lab

1. `curl -v http://localhost:8080/api/` — note response body and headers.
2. Temporarily remove trailing slash from `proxy_pass` — observe upstream path change.
3. Add `proxy_set_header X-Handbook-Day 3;` and verify with backend logs or `curl -v`.
4. Set `proxy_read_timeout 1s` and simulate slow backend — document 504/502 behavior.

---

## Day 3 checklist

- [ ] Understand `proxy_pass` slash behavior
- [ ] Set forwarding headers
- [ ] Tuned timeouts intentionally
- [ ] Know WebSocket proxy pattern

**Next:** [Day 4 — TLS](../day4/)
