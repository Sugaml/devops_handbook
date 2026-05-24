# Day 4 — TLS Termination & Certificate Management

**Goal:** Generate lab certificates, enable HTTPS on nginx, and apply TLS best-practice settings.

**Time:** 4–5 hours

---

## 1. TLS termination at the edge

```
Client --HTTPS--> nginx --HTTP--> app (internal network)
```

Certificates live on nginx (or cloud LB). Apps see `X-Forwarded-Proto: https`.

---

## 2. Generate lab certs

```bash
chmod +x day4/labs/gen-certs.sh
./day4/labs/gen-certs.sh
```

Copy `day4/labs/10-tls.conf.example` → `labs/conf/10-tls.conf`, then:

```bash
docker compose exec nginx nginx -t
docker compose exec nginx nginx -s reload
curl -k https://localhost:8443/
```

`-k` skips verification for self-signed certs.

---

## 3. Modern TLS settings

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 1d;
```

Production: use **Let's Encrypt** (certbot) or cloud-managed certs (ACM). Automate renewal.

---

## 4. HSTS

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

Only enable after HTTPS works everywhere — HSTS is hard to roll back.

---

## 5. certbot pattern (production reference)

```bash
certbot certonly --webroot -w /var/www/html -d app.example.com
# hooks: deploy hook runs nginx -s reload
```

In Kubernetes, use cert-manager + Ingress annotations instead.

---

## Lab

1. Generate certs and enable TLS vhost on 8443.
2. Test with `curl -vk https://localhost:8443/`.
3. Run `openssl s_client -connect localhost:8443 -servername localhost </dev/null 2>/dev/null | openssl x509 -noout -subject -dates`
4. Document renewal process for Let's Encrypt vs self-signed.
5. Break TLS (wrong cert path) — confirm `nginx -t` catches at reload.

---

## Day 4 checklist

- [ ] TLS listener serving on 8443
- [ ] Understand termination vs passthrough
- [ ] Know HSTS implications
- [ ] Tested cert validation with openssl

**Next:** [Day 5 — Caching](../day5/)
