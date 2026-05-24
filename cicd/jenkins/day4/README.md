# Day 4 — Credentials, Secrets & Environments

**Goal:** Store secrets in Jenkins Credentials, bind them safely in pipelines, and model staging/production with parameters and approval gates.

**Time:** 4–6 hours

---

## 1. Never hardcode secrets

```groovy
// BAD — never commit this
sh 'curl -H "Authorization: token ghp_xxxx" ...'
```

Use **Manage Jenkins → Credentials** (scoped by domain/folder).

| Kind | Use case |
|------|----------|
| Username/password | Basic auth, Git HTTPS |
| Secret text | API tokens, single strings |
| SSH private key | Git SSH, remote hosts |
| Secret file | kubeconfig, JSON key files |

---

## 2. Bind credentials in Pipeline

```groovy
pipeline {
    agent any

    environment {
        APP_ENV = 'staging'
    }

    stages {
        stage('Deploy') {
            when { branch 'main' }
            steps {
                withCredentials([string(credentialsId: 'staging-api-token', variable: 'API_TOKEN')]) {
                    sh '''
                        set +x
                        curl -sf -H "Authorization: Bearer ${API_TOKEN}" \
                          https://api.example.com/deploy?env=${APP_ENV}
                    '''
                }
            }
        }
    }
}
```

**Masking:** Jenkins masks `API_TOKEN` in logs when used via `withCredentials`. Still avoid `echo ${API_TOKEN}`.

---

## 3. Username/password binding

```groovy
withCredentials([usernamePassword(
    credentialsId: 'docker-hub',
    usernameVariable: 'DOCKER_USER',
    passwordVariable: 'DOCKER_PASS'
)]) {
    sh 'echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin'
}
```

---

## 4. Parameters and promoted builds

```groovy
pipeline {
    agent any

    parameters {
        choice(name: 'DEPLOY_ENV', choices: ['staging', 'production'], description: 'Target')
        booleanParam(name: 'DRY_RUN', defaultValue: true, description: 'Skip real deploy')
    }

    stages {
        stage('Deploy') {
            steps {
                echo "Deploying to ${params.DEPLOY_ENV}, dry_run=${params.DRY_RUN}"
            }
        }
    }
}
```

**Input step (manual approval):**

```groovy
stage('Approve Production') {
    when {
        allOf {
            branch 'main'
            expression { params.DEPLOY_ENV == 'production' }
        }
    }
    steps {
        input message: 'Deploy to production?', ok: 'Deploy'
    }
}
```

---

## 5. Folder-scoped credentials

Organize jobs under folders (`team-a/staging`, `team-a/prod`). Credentials in folder `team-a/prod` are not visible to `team-a/dev` jobs when permissions are configured (Day 7 RBAC).

---

## 6. Credentials from external stores

Plugins integrate **HashiCorp Vault**, **AWS Secrets Manager**, **Azure Key Vault**. Pattern: fetch at runtime, short TTL, no secret in Git.

---

## 7. Lab — Day 4

1. Create **Secret text** credential `handbook-staging-token` with value `demo-token-not-real`.
2. Add Deploy stage (stub) using `withCredentials`; echo deploy URL without printing token.
3. Add `parameters { choice DEPLOY_ENV }` and `input` for production.
4. Break build by wrong `credentialsId`; fix and verify masking in console.

**Stretch:** Use **Credentials Binding** plugin with a hudson.util.Secret` patterns from official docs for file credentials.

---

## 8. DevOps connections

- **Separation of duties:** Developers merge; production deploy requires approver group (input + RBAC).
- **Rotation:** External secret store + credential ID stable in Jenkinsfile; rotate value in vault only.

---

## Quick reference

| Task | API |
|------|-----|
| Secret string | `string(credentialsId: 'id', variable: 'VAR')` |
| User/pass | `usernamePassword(...)` |
| Manual gate | `input message: '...'` |

**Prev:** [Day 3](../day3/) · **Next:** [Day 5 — Docker & artifacts](../day5/)
