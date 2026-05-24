# Day 2 — Virtual Hosts, Upstreams & Load Balancing

**Goal:** Configure upstream groups, observe load-balancing algorithms, and tune health-oriented proxy settings.

**Time:** 4 hours

---

## 1. Upstream block

```nginx
upstream handbook_api {
    least_conn;                    # round_robin (default), ip_hash, least_conn
    server backend1:5678;
    server backend2:5678;
}
```

Lab upstream is in `labs/conf/00-handbook.conf`.

---

## 2. Load-balancing methods

| Method | Use case |
|--------|----------|
| `round_robin` | Even distribution, stateless apps |
| `least_conn` | Long-lived connections, varying latency |
| `ip_hash` | Sticky sessions to same backend |
| `hash $request_uri` | Cache partition by URL |

---

## 3. Backend health (patterns)

nginx open-source lacks full active health checks — options:

- **max_fails / fail_timeout** on `server` lines
- **Commercial / Ingress** controllers with health probes
- **External** health checker + dynamic upstream (advanced)

```nginx
server backend1:5678 max_fails=2 fail_timeout=10s;
```

---

## 4. Test load distribution

```bash
for i in $(seq 1 10); do curl -s http://localhost:8080/api/; echo; done
```

You should see `backend1 OK` and `backend2 OK` mixed (algorithm-dependent).

---

## Lab

1. Observe default `least_conn` distribution (10 requests).
2. Change to `ip_hash`; repeat from same client — note stickiness.
3. Stop `backend1`: `docker stop handbook-backend1` — see failures then recovery after restart.
4. Add `proxy_next_upstream error timeout` to `/api/` location and document when nginx retries.

---

## Day 2 checklist

- [ ] Explained three LB methods
- [ ] Tested upstream with both backends
- [ ] Simulated backend failure
- [ ] Know health-check limitations in open-source nginx

**Next:** [Day 3 — Reverse proxy](../day3/)
