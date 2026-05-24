# Day 5 — Docker Build, Push & Artifacts

**Goal:** Build and push container images to GHCR or Docker Hub; upload workflow artifacts.

**Time:** 5–6 hours

---

## 1. Build and push with Docker Buildx

```yaml
permissions:
  contents: read
  packages: write

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:${{ github.sha }}
            ghcr.io/${{ github.repository }}:latest
```

See [labs/docker.yml](./labs/docker.yml).

**GITHUB_TOKEN** can push to GHCR in same repo when `packages: write` is granted.

---

## 2. Docker Hub

```yaml
- uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```

Use **access token**, not account password.

---

## 3. Artifacts

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: |
      pytest-report.xml
    retention-days: 7
```

Download from Actions run summary; use for test reports, Terraform plans, etc.

---

## 4. Layer caching

```yaml
- uses: docker/build-push-action@v6
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

GitHub Actions cache backend speeds rebuilds.

---

## 5. Lab — Day 5

1. Add workflow building `sample-web` Dockerfile.
2. Push to `ghcr.io/YOUR_USER/sample-web:SHA`.
3. Pull locally and run container; hit `/health`.
4. Upload pytest JUnit XML as artifact (optional: generate with `--junitxml`).

---

## Quick reference

| Action | Purpose |
|--------|---------|
| `docker/login-action` | Registry auth |
| `docker/build-push-action` | Build + push |
| `upload-artifact` | Store files from run |

**Prev:** [Day 4](../day4/) · **Next:** [Day 6 — Reusable workflows & runners](../day6/)
