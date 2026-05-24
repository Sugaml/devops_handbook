# DevOps Handbook

Hands-on, day-by-day learning paths for tools and platforms used in modern DevOps and platform engineering. Each track includes theory, commands, labs, and production callouts.

## 7-day foundations

| Track | Description |
|-------|-------------|
| [Linux](./linux/) | Shell, systemd, networking, scripting |
| [Git](./git/) | Version control, branching, collaboration |
| [Docker](./docker/) | Containers, Compose, images, security |
| [Network](./network/) | IP, DNS, TCP, firewalls, TLS, VPCs |
| [NGINX](./nginx/) | Reverse proxy, TLS, caching, rate limits |
| [Ansible](./ansible/) | Configuration management and automation |
| [Terraform](./terraform/) | Infrastructure as code (week 1) |
| [Helm](./helm/) | Kubernetes package manager |
| [Argo CD](./argocd/) | GitOps continuous delivery |
| [Monitoring](./monitoring/) | Prometheus, Grafana, Loki, alerting |
| [Redis CLI](./rediscli/) | Redis operations and troubleshooting |
| [SQL](./sql/) | PostgreSQL for operators |

## CI/CD (4 platforms × 7 days)

| Track | Folder |
|-------|--------|
| Overview | [cicd/](./cicd/) |
| Jenkins | [cicd/jenkins/](./cicd/jenkins/) |
| GitHub Actions | [cicd/github/](./cicd/github/) |
| GitLab CI | [cicd/gitlab/](./cicd/gitlab/) |
| Bitbucket Pipelines | [cicd/bitbucket/](./cicd/bitbucket/) |

## Cloud providers

| Provider | Scope | Folder |
|----------|--------|--------|
| AWS | 30-day track | [aws/](./aws/) |
| GCP | 7-day foundation | [gcp/](./gcp/) |
| Azure | 7-day foundation | [azure/](./azure/) |

## Extended tracks

| Track | Scope | Folder |
|-------|--------|--------|
| Kubernetes | 30 days | [kubernetes/](./kubernetes/) |
| Python for DevOps | 30 days | [python/](./python/) |

## Suggested learning order

```
Linux → Git → Docker → Network
         ↓
    Pick one: Terraform / Ansible / CI/CD track
         ↓
    Kubernetes + Helm + Argo CD
         ↓
    Cloud (AWS/GCP/Azure) + Monitoring + SQL/Redis as needed
```

## How tracks are organized

- **`README.md`** — curriculum table and prerequisites
- **`DESIGN.md`** — decisions, ports, edge cases (where present)
- **`dayN/README.md`** — daily lesson and lab
- **`dayN/labs/`** or **`labs/`** — configs, scripts, sample apps

## Contributing / extending

Each track's `DESIGN.md` captures curriculum decisions and lab port maps. Add user feedback notes there when you extend content.

## License

Use for self-study and internal training. Replace placeholder hosts, credentials, and CIDRs before applying patterns to production.
