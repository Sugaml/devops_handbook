# Day 5 — Caching, Compression & Static Performance

**Goal:** Enable gzip, configure proxy cache zones, and set cache-control headers for static assets.

**Time:** 4 hours

---

## 1. Gzip compression

```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 256;
```

Trade CPU for bandwidth — disable for already-compressed formats (images, video).

---

## 2. Proxy cache

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 1m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
    add_header X-Cache-Status $upstream_cache_status;
    proxy_pass http://handbook_api/;
}
```

`$upstream_cache_status`: MISS, HIT, BYPASS, EXPIRED.

---

## 3. Browser caching (static)

```nginx
location ~* \.(css|js|png|jpg)$ {
    expires 7d;
    add_header Cache-Control "public, immutable";
}
```

Use **cache busting** via filename hash in CI (`app.a1b2c3.js`).

---

## Lab

1. Enable gzip in a new snippet `day5/labs/05-gzip.conf` — verify with `curl -H 'Accept-Encoding: gzip' -I`.
2. Add proxy cache zone for `/api/` (short TTL) — hit endpoint twice, compare `X-Cache-Status`.
3. Add `expires` for static site A assets.
4. Document one case where caching **must not** be used (authenticated API, POST).

---

## Day 5 checklist

- [ ] Enabled gzip safely
- [ ] Configured proxy_cache zone
- [ ] Set static asset cache headers
- [ ] Listed cache anti-patterns

**Next:** [Day 6 — Rate limiting & security](../day6/)
