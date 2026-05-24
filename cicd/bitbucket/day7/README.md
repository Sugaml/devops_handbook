# Day 7 — Production Bitbucket Pipelines: Governance, Cost & Troubleshooting

**Goal:** Operate Pipelines at workspace scale—minute budgets, security, Bitbucket Server differences, and on-call runbooks.

**Time:** 5–7 hours

---

## 1. Production checklist

```
[ ] Secured variables for all tokens; no secrets in YAML
[ ] Required PR builds before merge to main
[ ] Production deployment manual + restricted users
[ ] Docker service memory sized for real images
[ ] Pipes pinned to semver tags
[ ] Workspace audit log reviewed
[ ] Minute usage alerts configured
[ ] Self-hosted runners (Data Center) patched if used
```

---

## 2. Workspace administration

**Workspace settings → Pipelines:**

- Default image and max time limits
- SSH keys for deployment (read-only deploy keys per repo)
- OAuth credentials for AWS/GCP/Azure

**Repository variables** inherit; **deployment variables** override per environment.

---

## 3. Bitbucket Cloud vs Server/Data Center

| Feature | Cloud | Server/DC |
|---------|-------|-----------|
| Config file | `bitbucket-pipelines.yml` | Same (2.x+) |
| Runners | Atlassian-hosted | Self-hosted runners required |
| Pipes | Marketplace | Subset / custom |
| Minutes | Plan-based | Your infra |

Self-hosted runners: install on VM/K8s for private network deploys.

---

## 4. Cost optimization

- Use **caches** for pip/npm/maven
- **Parallel** only when it saves wall-clock worth minute cost
- Path-based skip scripts on monorepos
- `size: 2x` only when profiling proves need
- Schedule heavy jobs off-peak

---

## 5. Security

- Rotate secured variables quarterly
- Limit who can edit `bitbucket-pipelines.yml` on `main` (branch permissions)
- Scan images after push (add Trivy step or pipe)
- Review third-party pipes — they run with your secrets in scope

---

## 6. Troubleshooting

| Symptom | Fix |
|---------|-----|
| Docker build OOM | Increase `services.docker.memory`, use `size: 2x` |
| Pipe auth failed | Secured var name typo; scope |
| PR pipeline not running | Check `pull-requests` pattern; branch restriction |
| Cache not working | Cache key paths; first build populates |
| Minutes exhausted | Workspace plan; optimize or buy capacity |

**Enable debug:**

```yaml
script:
  - set -x
  - env | sort   # remove in prod — leaks non-secured vars
```

Use Bitbucket **Support tools → Log viewer** for runner issues (Data Center).

---

## 7. Lab — Day 7 capstone

1. Audit your pipeline YAML for unpinned pipes and hardcoded secrets.
2. Document workspace variable naming convention (`STAGING_*`, `PROD_*`).
3. Add branch restriction: 1 approval + green PR build for `main`.
4. Write runbook: "Pipeline minutes spike — investigation steps."

---

## 8. Four-platform summary

| Day | Jenkins | GitHub | GitLab | Bitbucket |
|-----|---------|--------|--------|-----------|
| 1 | Freestyle job | First workflow | `.gitlab-ci.yml` | First pipeline |
| 2 | Jenkinsfile | PR jobs | stages/rules | parallel steps |
| 3 | Docker agent | matrix/cache | runners | branch/PR triggers |
| 4 | credentials | secrets/env | CI variables | secured vars |
| 5 | docker.build | build-push-action | registry push | ECR pipe |
| 6 | multibranch | reusable wf | review apps | pipes + PR |
| 7 | HA/RBAC | org policies | child pipelines | workspace gov |

---

**Prev:** [Day 6](../day6/) · **Track home:** [Bitbucket README](../README.md) · **Handbook home:** [CI/CD README](../../README.md)
