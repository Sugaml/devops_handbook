# Day 6 — Multibranch Pipelines, Webhooks & PR Builds

**Goal:** Automatically discover branches and PRs, run Jenkinsfile per branch, and trigger builds from Git webhooks instead of polling.

**Time:** 5–6 hours

---

## 1. Multibranch Pipeline

One job scans Git and creates a sub-job per branch/PR with `Jenkinsfile` at repo root.

**New Item** → **Multibranch Pipeline** → name `sample-web-multibranch`

| Setting | Value |
|---------|--------|
| Branch Sources | GitHub / GitLab / Bitbucket |
| Credentials | SSH key or PAT with repo read |
| Behaviors | Discover branches, discover origin pull requests |
| Build configuration | by Jenkinsfile |

First scan may take minutes; each branch with Jenkinsfile gets a Pipeline.

---

## 2. Jenkinsfile for branches

```groovy
pipeline {
    agent {
        docker { image 'python:3.12-slim' }
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
        stage('Publish Preview') {
            when {
                not { branch 'main' }
            }
            steps {
                echo "Feature branch ${env.BRANCH_NAME} — skip prod push"
            }
        }
        stage('Push Image') {
            when { branch 'main' }
            steps {
                echo 'Push image — Day 5 logic'
            }
        }
    }
}
```

**Env vars:** `BRANCH_NAME`, `CHANGE_ID` (PR), `CHANGE_TARGET` (base branch).

---

## 3. Webhooks (GitHub example)

1. Install **GitHub plugin**
2. Manage Jenkins → Configure System → GitHub Server → add credentials
3. Multibranch job → scan triggers → **Build when change is pushed via GitHub hook**
4. GitHub repo → Settings → Webhooks → `https://JENKINS_URL/github-webhook/`

**Skip polling:** Remove `H/5 * * * *` SCM polling—webhooks are instant and cheaper.

---

## 4. PR status checks

GitHub plugin reports commit status back to PR. Required checks in branch protection:

- Repo → Settings → Branches → `main` → Require status check `Jenkinsfile` / job name

---

## 5. Organization Folder

For many repos: **New Item** → **GitHub Organization** → scans all repos matching pattern `.*-service` automatically.

---

## 6. Lab — Day 6

1. Convert Pipeline job to **Multibranch Pipeline** connected to your Git host.
2. Push feature branch with intentional test failure — verify PR/branch build fails.
3. Fix and push — verify green; merge to `main` — verify main-only stages run.
4. Configure webhook; push empty commit — build starts within seconds.

**Stretch:** Add `Jenkinsfile` stage that comments PR via GitHub API (use credential).

---

## 7. DevOps connections

- **Trunk-based development:** Short-lived branches + mandatory CI on PR.
- **Fork safety:** Do not expose production credentials to PRs from forks (same as GitHub Actions Day 6).

---

## Quick reference

| Concept | Item type |
|---------|-----------|
| Per-branch CI | Multibranch Pipeline |
| Many repos | Organization Folder |
| PR builds | Branch source behavior "Discover pull requests" |

**Prev:** [Day 5](../day5/) · **Next:** [Day 7 — Production Jenkins](../day7/)
