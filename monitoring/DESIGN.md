# Monitoring Handbook — Design Notes

## Curriculum arc

| Day | Skill level | Focus |
|-----|-------------|--------|
| 1 | Beginner | Three pillars, pull model, `/targets` health |
| 2 | Beginner+ | PromQL mental model, `rate`, `histogram_quantile` intro |
| 3 | Intermediate | Dashboards as code, variables, units |
| 4 | Intermediate | Alert design, routing, silences |
| 5 | Intermediate | Logs + metrics correlation |
| 6 | Advanced | Exporters, probes, SD patterns |
| 7 | Professional | SLOs, runbooks, capstone incident |

## Lab port map

| Port | Service |
|------|---------|
| 9090 | Prometheus |
| 3000 | Grafana |
| 9093 | Alertmanager |
| 3100 | Loki |
| 9100 | node-exporter |
| 8080 | handbook demo app (nginx) |
| 9115 | blackbox-exporter (Day 6) |

## Decisions

- **Single `docker-compose.yml`** at track root — simpler than per-day compose files for a 7-day arc.
- **No persistent Grafana edits in git** — provisioning under `labs/grafana/provisioning/`; learners may UI-tweak locally.
- **Alertmanager `webhook` receiver** — logs to stdout in lab; swap for Slack/PagerDuty in production.
- **Loki single-binary** — not production HA; teaches log labels and LogQL basics only.

## Edge cases

- macOS Docker Desktop: `host.docker.internal` used for scraping host-published ports when needed.
- High-cardinality labels (`user_id`, `request_id`) called out as anti-patterns on Day 2 and 7.
- Recording rules must load before alert rules that reference them — order in `prometheus.yml` rule_files.

## User feedback

_(Add notes here as you extend the handbook.)_
