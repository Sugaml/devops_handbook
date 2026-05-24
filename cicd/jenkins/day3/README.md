# Day 3 — Jenkins Agents, Labels & Docker

**Goal:** Run builds on dedicated agents and Docker containers; use labels, parallelism, and workspace hygiene for scalable CI.

**Time:** 4–6 hours

---

## 1. Controller vs agent (production rule)

**Never run heavy builds on the controller in production.** The controller holds secrets, plugins, and the queue—it should stay stable.

| Pattern | When |
|---------|------|
| `agent any` | Learning only; small teams with one agent |
| `agent { label 'linux' }` | Static VM agents |
| `agent { docker { image 'python:3.12' } }` | Reproducible toolchains |
| `agent { kubernetes { ... } }` | K8s plugin; dynamic pods |

---

## 2. Add a static agent (SSH)

**Manage Jenkins → Nodes → New Node**

- Name: `agent-linux-1`
- Type: Permanent Agent
- Remote root directory: `/home/jenkins/agent`
- Labels: `linux docker`
- Launch: SSH → host, credentials

On agent machine:

```bash
sudo useradd -m jenkins
# Install Java 17, git, python3, docker (if needed)
```

In Jenkinsfile:

```groovy
pipeline {
    agent { label 'linux' }
    // ...
}
```

---

## 3. Docker agent (no separate VM)

Requires **Docker Pipeline** plugin and Docker socket on agent (or Docker-in-Docker).

```groovy
pipeline {
    agent {
        docker {
            image 'python:3.12-slim'
            args '-v pip-cache:/root/.cache/pip'
        }
    }
    stages {
        stage('Test') {
            steps {
                sh '''
                    pip install -r requirements.txt
                    pytest -v
                '''
            }
        }
    }
}
```

**Pin images:** `python:3.12-slim@sha256:...` for supply-chain safety (Day 7).

---

## 4. Parallel stages

```groovy
stage('Test') {
    parallel {
        stage('Unit') {
            steps {
                sh 'pytest tests/ -v'
            }
        }
        stage('Lint') {
            steps {
                sh 'pip install flake8 && flake8 src/ || true'
            }
        }
    }
}
```

Use parallel when stages are independent; avoid overloading small agent pools.

---

## 5. Caching dependencies

```groovy
pipeline {
    agent {
        docker {
            image 'python:3.12-slim'
            reuseNode true
        }
    }
    stages {
        stage('Test') {
            steps {
                sh '''
                    pip install -r requirements.txt -q
                    pytest -v
                '''
            }
        }
    }
}
```

For persistent cache across builds, mount volumes or use **Pipeline Utility Steps** / Nexus / Artifactory. Cloud-native platforms often have first-class cache (compare GitHub Day 3).

---

## 6. Workspace and cleanWs

```groovy
post {
    always {
        cleanWs()
    }
}
```

Prevents disk fill on long-lived agents. Use **skipDefaultCheckout** + custom checkout only when you understand implications.

---

## 7. Lab — Day 3

1. Convert Day 2 Jenkinsfile to use `agent { docker { image 'python:3.12-slim' } }`.
2. Add parallel **Unit** and **Lint** stages.
3. (Optional) Register a second node with label `linux`; route pipeline with `agent { label 'linux' }`.
4. Verify build runs in container (`cat /etc/os-release` in sh step).

**Stretch:** Different Docker image for a **Node.js lint** stage using `agent none` + stage-level `agent { docker { image 'node:20-alpine' } }`.

---

## 8. DevOps connections

- **Ephemeral agents:** K8s/EKS agents scale to zero—pay for compute only during builds.
- **Tool drift:** Docker agents eliminate "works on agent 3 only" problems.

---

## Quick reference

| Directive | Example |
|-----------|---------|
| Label agent | `agent { label 'linux' }` |
| Docker agent | `agent { docker { image 'img:tag' } }` |
| Parallel | `parallel { stage('A'){...} stage('B'){...} }` |

**Prev:** [Day 2](../day2/) · **Next:** [Day 4 — Credentials & environments](../day4/)
