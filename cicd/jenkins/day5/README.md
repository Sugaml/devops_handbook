# Day 5 — Docker Builds, Artifacts & Registry Push

**Goal:** Build a Docker image in Jenkins, tag with Git commit SHA, push to a registry, and archive build artifacts.

**Time:** 5–6 hours

---

## 1. CI output = immutable artifact

```
git commit → CI → docker build → push registry:sample-web:abc1234
                                      ↓
                              CD deploys exact tag
```

Rebuild in CD is an anti-pattern—promote the **same** image digest.

---

## 2. Install plugins

- **Docker Pipeline**
- **Docker** (cloud/agents optional)
- **Pipeline Utility Steps** (optional, for archiving)

Ensure Docker CLI available on agent (or use Docker agent with mounted socket—understand security implications).

---

## 3. Build and tag

```groovy
pipeline {
    agent any

    environment {
        IMAGE_NAME = 'your-dockerhub-user/sample-web'
        GIT_SHORT = "${env.GIT_COMMIT?.take(7) ?: 'local'}"
    }

    stages {
        stage('Test') {
            steps {
                sh '''
                    python3 -m venv .venv && . .venv/bin/activate
                    pip install -r requirements.txt
                    pytest -v
                '''
            }
        }
        stage('Build Image') {
            steps {
                script {
                    docker.build("${IMAGE_NAME}:${GIT_SHORT}")
                }
            }
        }
        stage('Push') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'docker-hub',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push ${IMAGE_NAME}:${GIT_SHORT}
                        docker tag ${IMAGE_NAME}:${GIT_SHORT} ${IMAGE_NAME}:latest
                        docker push ${IMAGE_NAME}:latest
                    '''
                }
            }
        }
    }
}
```

See [labs/Jenkinsfile](./labs/Jenkinsfile).

---

## 4. Archive artifacts (non-Docker)

```groovy
stage('Package') {
    steps {
        sh 'tar czf dist.tar.gz src/ requirements.txt'
        archiveArtifacts artifacts: 'dist.tar.gz', fingerprint: true
    }
}
```

**Fingerprint:** Track which builds consumed which artifact across jobs.

---

## 5. docker.withRegistry

Cleaner login wrapper:

```groovy
script {
    docker.withRegistry('https://index.docker.io/v1/', 'docker-hub') {
        def img = docker.build("${IMAGE_NAME}:${GIT_SHORT}")
        img.push()
        img.push('latest')
    }
}
```

For **GHCR/ECR**, change registry URL and credential type (often username/password or AWS plugin).

---

## 6. Security notes

- Use **minimal base images** (`python:3.12-slim`).
- Scan images (Trivy, Clair) in a later stage or external policy.
- Do not run Docker socket on controller.

---

## 7. Lab — Day 5

1. Add Docker build stage after tests; tag `sample-web:${GIT_SHORT}`.
2. Create Docker Hub credential; push from `main` only.
3. Pull image locally: `docker pull user/sample-web:SHA`.
4. Archive `requirements.txt` + test report as artifacts.

**Stretch:** Add stage running `docker run --rm image pytest` for "test in image" validation.

---

## 8. DevOps connections

- **Traceability:** Image tag = Git SHA → incident rollback is `kubectl set image ...:oldsha`.
- **Registry as handoff** between CI (build) and CD (GitOps/Helm values update).

---

## Quick reference

| Task | Groovy |
|------|--------|
| Build | `docker.build('name:tag')` |
| Push with cred | `docker.withRegistry(url, credId) { img.push() }` |
| Archive | `archiveArtifacts artifacts: 'path'` |

**Prev:** [Day 4](../day4/) · **Next:** [Day 6 — Multibranch & webhooks](../day6/)
