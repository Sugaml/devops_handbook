# Day 2 — Declarative Pipeline & Jenkinsfile

**Goal:** Replace GUI freestyle jobs with **Pipeline as Code**—stages, steps, post actions, and a Jenkinsfile stored in Git.

**Time:** 4–6 hours

---

## 1. Why Pipeline as Code?

- **Review:** CI changes go through PRs like application code.
- **Reproduce:** Same `Jenkinsfile` on every branch.
- **Audit:** Git history shows who changed deploy steps.

Two syntaxes: **Declarative** (structured, recommended) and **Scripted** (Groovy-heavy). This handbook uses Declarative.

---

## 2. Minimal Jenkinsfile

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Test') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install -r requirements.txt
                    pytest -v
                '''
            }
        }
    }

    post {
        success {
            echo 'Pipeline succeeded'
        }
        failure {
            echo 'Pipeline failed — check console'
        }
        always {
            cleanWs()
        }
    }
}
```

Save as `Jenkinsfile` in repo root. See [labs/Jenkinsfile](./labs/Jenkinsfile).

---

## 3. Create a Pipeline job

1. **New Item** → `handbook-day2-pipeline` → **Pipeline** → OK
2. **Pipeline** section:
   - Definition: **Pipeline script from SCM**
   - SCM: Git → repo URL → branch `*/main`
   - Script Path: `Jenkinsfile`
3. Save → Build Now

**Pipeline runs from repo**, not pasted Groovy in the UI (except for quick experiments).

---

## 4. Stages and steps

```
pipeline
  └── stages
        ├── stage('Build')
        │     └── steps { sh '...' }
        ├── stage('Test')
        └── stage('Deploy')  // Day 4+
```

| Directive | Purpose |
|-----------|---------|
| `agent any` | Run on any available executor |
| `stage('Name')` | Logical phase; visible in Blue Ocean / Stage View |
| `steps { }` | Actual commands |
| `post { }` | Runs after stages (success/failure/always) |

**Fail fast:** Put lint/quick tests in early stages.

---

## 5. Options and timeouts

```groovy
pipeline {
    agent any

    options {
        buildDiscarder(logRotatingNumToKeepStr: '10')
        timeout(time: 15, unit: 'MINUTES')
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Test') {
            steps {
                sh 'pytest -v'  // intentional typo → fails
            }
        }
    }
}
```

---

## 6. When / conditions

```groovy
stage('Deploy Staging') {
    when {
        branch 'main'
    }
    steps {
        echo 'Deploy stub — Day 4'
    }
}
```

Branch conditions matter for CD gates (Day 4–6).

---

## 7. Stage View and Blue Ocean

- **Stage View:** Classic UI on Pipeline job — time per stage.
- **Blue Ocean:** Visual pipeline (install **Blue Ocean** plugin); good for demos.

```bash
# Optional: open Blue Ocean from Jenkins sidebar after plugin install
```

---

## 8. Linting Jenkinsfiles

Install **Pipeline Syntax** generator: job → **Pipeline Syntax** link (when editing Pipeline job).

Local validation (optional):

```bash
# jenkins-cli or IDE Groovy support; many teams rely on test multibranch + PR build
curl -s -F "jenkinsfile=<Jenkinsfile" https://YOUR_JENKINS/pipeline-model-converter/validate
# Requires authenticated Jenkins with converter endpoint
```

---

## 9. Lab — Day 2

1. Add [labs/Jenkinsfile](./labs/Jenkinsfile) to your `sample-web` repo; push.
2. Create Pipeline-from-SCM job pointing at `Jenkinsfile`.
3. Add stages: **Lint** (optional `flake8` or skip), **Test** (`pytest).
4. Add `post { failure { echo 'failed' }` — verify failure message on red build.
5. Add `options { timeout 10 MINUTES }`; verify Stage View.

**Stretch:** Split Test into **Unit** and **Integration** stages (same pytest command twice with different markers if you add markers later).

---

## 10. DevOps connections

- **PR checks:** Multibranch (Day 6) runs this Jenkinsfile per branch.
- **Same pipeline everywhere:** `Jenkinsfile` in repo = single source of truth for CI.

---

## Quick reference

| Task | Syntax |
|------|--------|
| Shell step | `sh 'command'` |
| Echo | `echo 'msg'` |
| SCM checkout | `checkout scm` |
| Keep logs | `buildDiscarder` in `options` |

**Prev:** [Day 1](../day1/) · **Next:** [Day 3 — Agents & Docker](../day3/)
