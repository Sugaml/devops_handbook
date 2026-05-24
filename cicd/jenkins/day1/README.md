# Day 1 — CI/CD Fundamentals & Your First Jenkins Job

**Goal:** Understand continuous integration and delivery, install Jenkins, and run a successful freestyle job that checks out code and executes a shell step.

**Time:** 4–6 hours (theory + hands-on)

---

## 1. What is CI/CD?

| Term | Meaning | DevOps outcome |
|------|---------|----------------|
| **CI (Continuous Integration)** | Merge code frequently; every change triggers automated build + test | Catch bugs minutes after commit, not days later |
| **CD (Continuous Delivery)** | Main branch is always deployable; release is a business decision (button click) | Predictable, low-risk releases |
| **CD (Continuous Deployment)** | Every green main build auto-deploys to production | Maximum velocity with strong guardrails |

```
Developer → git push → CI server → build → test → artifact
                                              ↓
                                    CD → staging → production
```

**Why Jenkins?**

- Self-hosted: runs in your VPC, air-gapped if needed.
- Huge plugin ecosystem (Git, Docker, Kubernetes, Slack, credentials).
- Mature **Pipeline as Code** (`Jenkinsfile`) for reviewable, versioned CI/CD.

Cloud-native alternatives (GitHub Actions, GitLab CI, Bitbucket Pipelines) trade self-hosting burden for managed runners and tighter Git integration. This track teaches Jenkins deeply; compare with other tracks in [../../README.md](../../README.md).

---

## 2. Jenkins architecture

```
                    ┌─────────────────────┐
                    │  Jenkins Controller │
                    │  (UI, scheduling,   │
                    │   plugins, config)  │
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │ Agent/Node  │     │ Agent/Node  │     │ Agent/Node  │
    │ (executes   │     │ (Docker     │     │ (K8s pod)   │
    │  build steps)│    │  agent)     │     │             │
    └─────────────┘     └─────────────┘     └─────────────┘
```

| Component | Role |
|-----------|------|
| **Controller** | Web UI (8080), job definitions, queue, credentials store |
| **Agent (node)** | Machine/container where build steps run |
| **Job / Pipeline** | Unit of work (freestyle, pipeline, multibranch) |
| **Plugin** | Extends Jenkins (Git, Pipeline, Docker, Blue Ocean) |
| **Workspace** | Per-build directory on agent (`$WORKSPACE`) |

**Day 1** uses the built-in controller executor (fine for learning; production separates agents on Day 3).

---

## 3. Install Jenkins (Docker — recommended)

```bash
docker volume create jenkins_home

docker run -d --name jenkins \
  --restart unless-stopped \
  -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  jenkins/jenkins:lts-jdk17

# Initial admin password (first boot only)
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

1. Open **http://localhost:8080**
2. Paste initial password → **Install suggested plugins**
3. Create admin user → save Jenkins URL

**Verify:**

```bash
docker logs jenkins --tail 20
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/login
# 200
```

**Alternative (Linux package):** See [Jenkins install docs](https://www.jenkins.io/doc/book/installing/linux/) — prefer LTS + JDK 17.

---

## 4. Jenkins UI tour

| Area | Purpose |
|------|---------|
| **Dashboard** | All jobs; build weather icons |
| **New Item** | Create freestyle, pipeline, multibranch, etc. |
| **Manage Jenkins** | Plugins, nodes, credentials, system config |
| **Build History** | Console output, artifacts, timing |
| **Manage Jenkins → Plugins** | Install Git, Pipeline, Docker if missing |

Install **Git plugin** (usually bundled with suggested set).

---

## 5. Prepare sample application

```bash
cp -r ../../labs/sample-web /tmp/jenkins-day1-sample
cd /tmp/jenkins-day1-sample

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v

git init && git add . && git commit -m "chore: initial sample-web"
```

Push to GitHub/GitLab/Bitbucket, or use **file://** path for local-only freestyle jobs:

```bash
# Local path works for freestyle "Git" optional; for real CI use a remote
git remote add origin git@github.com:YOUR_USER/jenkins-handbook-day1.git
git push -u origin main
```

---

## 6. First freestyle job (GUI)

1. **New Item** → name `day1-hello` → **Freestyle project** → OK
2. **Source Code Management** → Git → Repository URL → your repo URL
3. **Branches to build** → `*/main`
4. **Build Steps** → **Execute shell**:

```bash
#!/usr/bin/env bash
set -euo pipefail
echo "BUILD_NUMBER=${BUILD_NUMBER}"
echo "GIT_COMMIT=${GIT_COMMIT:-local}"
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
pytest -v
echo "Build succeeded on $(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

5. **Save** → **Build Now**
6. Click build number → **Console Output**

**Environment variables Jenkins injects:**

| Variable | Example |
|----------|---------|
| `BUILD_NUMBER` | `3` |
| `JOB_NAME` | `day1-hello` |
| `WORKSPACE` | `/var/jenkins_home/workspace/day1-hello` |
| `GIT_COMMIT` | Full SHA (when Git SCM configured) |
| `BUILD_URL` | Link to this build |

---

## 7. Freestyle vs Pipeline

| Freestyle | Pipeline (Jenkinsfile) |
|-----------|----------------------|
| GUI-configured | Code in Git |
| Hard to review in PRs | Diffable, reusable |
| OK for one-off tasks | Standard for teams |

**DevOps standard:** Pipeline as Code from Day 2 onward. Freestyle teaches how steps map to shell on an agent.

---

## 8. Triggering builds

| Trigger | Setup |
|---------|--------|
| Manual | Build Now |
| SCM polling | `H/5 * * * *` in job (avoid in production — use webhooks Day 6) |
| Webhook | GitHub → Jenkins GitHub plugin (Day 6) |
| Upstream | Trigger after another job |

---

## 9. Lab — Day 1

1. Install Jenkins via Docker; complete setup wizard.
2. Create freestyle job `handbook-day1-test` from your `sample-web` repo.
3. Add shell step: install deps + `pytest -v`; confirm green build.
4. Intentionally break a test in Git; push; rebuild — confirm **FAILED** and read console log.
5. Fix test; rebuild — confirm green.
6. Note `BUILD_NUMBER` and workspace path from console output.

**Stretch:** Install **Timestamper** plugin; rebuild and see per-line timestamps in console.

---

## 10. DevOps connections

- **Immutable artifacts:** CI proves a commit passes tests; CD promotes the **same** artifact (image SHA), not a rebuild.
- **Fast feedback:** Target <10 min for PR feedback on small services.
- **Blameless culture:** Red builds are team problems; Jenkins history shows *when* regression entered.

---

## Quick reference

| Task | Where |
|------|--------|
| Initial password | `secrets/initialAdminPassword` in `JENKINS_HOME` |
| New job | Dashboard → New Item |
| Console log | Job → Build #N → Console Output |
| Plugins | Manage Jenkins → Plugins |

**Next:** [Day 2 — Declarative Pipeline & Jenkinsfile](../day2/)
