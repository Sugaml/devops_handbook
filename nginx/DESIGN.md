# NGINX Handbook — Design Notes

## Curriculum arc

| Day | Focus |
|-----|--------|
| 1 | Mental model: events, http, server, location |
| 2 | Multi-site and upstream LB |
| 3 | App proxy patterns (headers, timeouts) |
| 4 | TLS and modern cipher hygiene |
| 5 | Performance (cache, gzip) |
| 6 | Edge security controls |
| 7 | Ops: logs, metrics, incident debug |

## Lab port map

| Port | Purpose |
|------|---------|
| 8080 | Reverse proxy entry (API demo) |
| 8081 | Static site A |
| 8082 | Static site B |
| 8443 | TLS vhost (Day 4+) |
| 9001–9002 | Upstream backend containers |

## Decisions

- **Single nginx container** with `include /etc/nginx/conf.d/*.conf` — mirrors distro layout.
- **Backend containers** (`backend1`, `backend2`) return distinct bodies for LB verification.
- **Self-signed certs** generated in `day4/labs/gen-certs.sh` — not committed (gitignored pattern documented).

## Edge cases

- `nginx -t` must pass before reload — broken config leaves old config active.
- `proxy_pass` trailing slash changes URI path — Day 3 calls this out explicitly.
- `limit_req` applies per-worker in some versions — document burst for real capacity planning.

## User feedback

_(Add notes here as you extend the handbook.)_
