# Day 5 — Docker Build, Registry Push & Artifacts

**Goal:** Build and push images to Docker Hub or AWS ECR using Pipelines services and pipes; save build artifacts.

**Time:** 5–6 hours

---

## 1. Docker build and push (manual login)

```yaml
definitions:
  services:
    docker:
      memory: 3072

pipelines:
  branches:
    main:
      - step:
          name: Build and push
          services:
            - docker
          script:
            - echo "$DOCKERHUB_PASSWORD" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin
            - export IMAGE=youruser/sample-web:${BITBUCKET_COMMIT:0:7}
            - docker build -t $IMAGE .
            - docker push $IMAGE
```

Store `DOCKERHUB_USERNAME` / `DOCKERHUB_PASSWORD` as secured variables.

---

## 2. AWS ECR pipe (Atlassian marketplace)

```yaml
- step:
    name: Push to ECR
    services:
      - docker
    script:
      - docker build -t myapp .
      - pipe: atlassian/aws-ecr-push-image:2.4.0
        variables:
          AWS_ACCESS_KEY_ID: $AWS_ACCESS_KEY_ID
          AWS_SECRET_ACCESS_KEY: $AWS_SECRET_ACCESS_KEY
          AWS_DEFAULT_REGION: us-east-1
          IMAGE_NAME: myapp
          TAGS: ${BITBUCKET_COMMIT:0:7}
```

Prefer OIDC/IAM roles when Bitbucket supports your cloud setup; rotate keys if using static credentials.

See [labs/bitbucket-pipelines.yml](./labs/bitbucket-pipelines.yml).

---

## 3. Artifacts

```yaml
- step:
    name: Test
    script:
      - pip install -r requirements.txt
      - pytest -v --junitxml=junit.xml
    artifacts:
      - junit.xml
```

Download artifacts from pipeline summary; retention per workspace policy.

---

## 4. Image size and step size

```yaml
- step:
    size: 2x    # double memory/CPU — costs 2x minutes
    services:
      - docker:
          memory: 4096
```

Large Docker builds often need `2x` and increased docker service memory.

---

## 5. Lab — Day 5

1. Build and push `sample-web` image tagged with short commit SHA.
2. Pull and run container locally.
3. Save pytest output as artifact.
4. (Optional) Use ECR pipe instead of Docker Hub.

---

## Quick reference

| Item | Syntax |
|------|--------|
| Artifacts | `artifacts:` list under step |
| Pipe | `pipe: vendor/name:version` |
| Larger build | `size: 2x` |

**Prev:** [Day 4](../day4/) · **Next:** [Day 6 — Pipes & PR integrations](../day6/)
