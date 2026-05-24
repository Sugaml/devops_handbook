# Day 5 — Docker Build, GitLab Container Registry & Cache

**Goal:** Build and push images to GitLab Container Registry, use Kaniko or Docker-in-Docker, and optimize cache/artifacts.

**Time:** 5–6 hours

---

## 1. GitLab Container Registry

Each project: `registry.gitlab.com/group/project`

```yaml
variables:
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA

build:
  stage: build
  image: docker:24-cli
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" $CI_REGISTRY
  script:
    - docker build -t "$IMAGE_TAG" .
    - docker push "$IMAGE_TAG"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

`CI_REGISTRY_*` credentials injected automatically.

See [labs/.gitlab-ci.yml](./labs/.gitlab-ci.yml).

---

## 2. Kaniko (no Docker socket)

```yaml
build:
  image:
    name: gcr.io/kaniko-project/executor:debug
    entrypoint: [""]
  script:
    - /kaniko/executor
      --context "${CI_PROJECT_DIR}"
      --dockerfile "${CI_PROJECT_DIR}/Dockerfile"
      --destination "${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}"
```

Better for shared runners without privileged DinD.

---

## 3. Artifacts

```yaml
test:
  script:
    - pytest --junitxml=report.xml
  artifacts:
    when: always
    reports:
      junit: report.xml
    expire_in: 1 week
```

JUnit reports show in MR **Tests** tab.

---

## 4. Cache vs artifacts

| Feature | Purpose |
|---------|---------|
| **cache** | Speed up next pipeline (deps) |
| **artifacts** | Pass files between stages / download |

```yaml
cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - .cache/pip
```

---

## 5. Lab — Day 5

1. Add build job pushing to project registry.
2. Pull image: `docker pull registry.gitlab.com/group/project:sha`
3. Add JUnit artifact from pytest.
4. (Optional) Switch DinD to Kaniko.

---

## Quick reference

| Variable | Meaning |
|----------|---------|
| `CI_REGISTRY` | Registry hostname |
| `CI_REGISTRY_IMAGE` | Full image path |
| `CI_REGISTRY_USER/PASSWORD` | Job login |

**Prev:** [Day 4](../day4/) · **Next:** [Day 6 — Environments & review apps](../day6/)
