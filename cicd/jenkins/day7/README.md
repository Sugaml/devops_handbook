# Day 7 — Production Jenkins: HA, Security & Troubleshooting

**Goal:** Operate Jenkins like a platform team—high availability, RBAC, backup, plugin hygiene, and systematic debugging of failed pipelines.

**Time:** 5–7 hours

---

## 1. Production architecture

```
                    ┌──────────────────┐
                    │  Load balancer   │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
     ┌─────────────────┐           ┌─────────────────┐
     │ Controller (active)│         │ Controller (standby)│  ← optional HA
     └────────┬────────┘           └─────────────────┘
              │
    ┌─────────┴─────────┬─────────────┐
    ▼                   ▼             ▼
 Agent pool         K8s agents    Cloud agents (EC2)
```

| Principle | Practice |
|-----------|----------|
| Controller is sacred | No builds on controller; limit plugins |
| Agents ephemeral | Recycle VMs/containers; cleanWs |
| Config as code | **JCasC** (Jenkins Configuration as Code) + Job DSL / multibranch |
| Backups | `JENKINS_HOME` volume snapshots daily |

---

## 2. Jenkins Configuration as Code (JCasC)

Export config to YAML in Git; bootstrap new controllers from repo.

```yaml
# jcasc/credentials-example.yaml (illustrative — use JCasC export)
jenkins:
  systemMessage: "Production Jenkins — handbook example"
  numExecutors: 0   # controller runs zero builds
unclassified:
  location:
    url: "https://jenkins.company.com/"
```

Install **Configuration as Code** plugin; **Manage Jenkins → Configuration as Code**.

---

## 3. RBAC (Role-based Strategy)

Install **Role-based Authorization Strategy**:

| Role | Permissions |
|------|-------------|
| Developer | Read, build, cancel own jobs |
| Release manager | Deploy jobs + input approve |
| Admin | Full |

Map LDAP/OAuth groups to roles; avoid local user sprawl.

---

## 4. Security hardening checklist

- [ ] HTTPS only; reverse proxy (nginx/ALB) with TLS
- [ ] Disable anonymous read (unless public OSS)
- [ ] CSRF protection enabled (default)
- [ ] Agent → controller over JNLP/WebSocket on 50000-50400; restrict SG/firewall
- [ ] Pin plugins; monthly update window with rollback plan
- [ ] Audit log plugin → SIEM
- [ ] No Docker socket on shared agents without isolation
- [ ] Credentials scoped per folder; production creds only on prod folder jobs
- [ ] Script approval for Pipeline shared libraries

---

## 5. Shared libraries

Reusable Groovy in Git:

```groovy
// vars/buildPythonApp.groovy
def call(Map config) {
    pipeline {
        agent { docker { image config.image ?: 'python:3.12-slim' } }
        stages {
            stage('Test') {
                steps { sh 'pytest -v' }
            }
        }
    }
}
```

Configure: **Manage Jenkins → System → Global Pipeline Libraries**.

---

## 6. Troubleshooting playbook

| Symptom | Checks |
|---------|--------|
| Queue stuck | Manage Jenkins → Build Queue; agent offline? labels match? |
| `Cannot connect to agent` | SSH key, firewall, Java version on agent |
| Intermittent Git failures | Credential expiry, rate limits, shallow clone |
| OOM during Docker build | Agent memory; limit parallel builds |
| Plugin upgrade broke builds | Pin versions; test in staging controller |

**Useful commands:**

```bash
# Controller shell (Docker)
docker exec -it jenkins bash
tail -f /var/jenkins_home/logs/jenkins.log

# Thread dump from UI: /threadDump
# System info: /systemInfo
```

**Pipeline replay:** Re-run failed build with same commit but editable Groovy (debug only—not for prod changes).

---

## 7. Observability

- **Prometheus plugin** — metrics (queue length, executor usage)
- **Datadog / CloudWatch** — log shipping from agents
- Alert on: queue time > 15m, failure rate spike, disk > 85% on `JENKINS_HOME`

---

## 8. Lab — Day 7 capstone

1. Set controller **# executors = 0**; route all builds to Docker agent.
2. Document RBAC matrix for your lab (3 roles).
3. Export JCasC snippet for `numExecutors: 0` and location URL.
4. Simulate failure modes: stop agent → observe queue; wrong label → fix.
5. Write runbook section: "How we restore Jenkins from backup" (volume snapshot steps).

**Production checklist (self-grade):**

```
[ ] Pipeline as Code only (no freestyle prod jobs)
[ ] Webhooks not polling
[ ] Secrets in credential store / Vault
[ ] Images tagged with Git SHA
[ ] Branch protection + required Jenkins check
[ ] Backups tested restore this quarter
[ ] Plugin update runbook exists
```

---

## 9. When to choose Jenkins vs cloud CI

| Choose Jenkins | Choose GitHub/GitLab/Bitbucket CI |
|----------------|-----------------------------------|
| Strict data residency / air-gap | Git-native, zero controller ops |
| Custom integrations / legacy | Fast start, managed runners |
| Central CI for many VCS systems | Single VCS vendor |

Many enterprises run **both**: cloud CI for app repos, Jenkins for specialized mainframe/build farms.

---

## Quick reference

| Task | Location |
|------|----------|
| JCasC | Manage Jenkins → Configuration as Code |
| RBAC | Manage Jenkins → Security → Authorization |
| Backup | Snapshot `JENKINS_HOME` |
| Replay | Build page → Replay |

**Prev:** [Day 6](../day6/) · **Track home:** [Jenkins README](../README.md)
