# Day 6 — Pipes, Integrations & Pull Request Pipelines

**Goal:** Use Atlassian pipes for common tasks, integrate Jira/Slack, and enforce PR quality gates.

**Time:** 5–6 hours

---

## 1. What are pipes?

Pre-packaged Docker steps from Atlassian/marketplace — like GitHub Actions but YAML-native to Bitbucket.

```yaml
- pipe: atlassian/slack-notify:2.3.0
  variables:
    WEBHOOK_URL: $SLACK_WEBHOOK_URL
    MESSAGE: "Build ${BITBUCKET_BUILD_NUMBER} finished on ${BITBUCKET_BRANCH}"
```

Browse: Bitbucket **Pipes** documentation and marketplace.

---

## 2. Common pipes

| Pipe | Purpose |
|------|---------|
| `atlassian/aws-s3-deploy` | Static site to S3 |
| `atlassian/aws-ecr-push-image` | Push to ECR |
| `atlassian/git-secrets-scan` | Secret scanning |
| `docker://hadolint/hadolint` | Dockerfile lint |

Always **pin pipe version** (`:2.4.0` not `:latest`).

---

## 3. PR pipeline + required builds

```yaml
pipelines:
  pull-requests:
    '**':
      - step:
          name: PR checks
          script:
            - pip install -r requirements.txt && pytest -v
      - step:
          name: Secret scan
          script:
            - pipe: atlassian/git-secrets-scan:1.4.0
```

**Repository settings → Branch permissions / Branch restrictions:**

- Require passing builds before merge
- Require approvals

See [labs/bitbucket-pipelines.yml](./labs/bitbucket-pipelines.yml).

---

## 4. Jira integration

Connect repo to Jira; include issue keys in commit messages (`PROJ-123`) for automatic linking. Deployment steps can transition issues when using Jira deployments feature.

---

## 5. Monorepo — changesets (Bitbucket Cloud)

Use conditional steps or separate repos; for path-based runs, custom scripts:

```yaml
script:
  - |
    if git diff --name-only HEAD~1 | grep -q '^services/api/'; then
      cd services/api && pytest
    else
      echo "Skipping api tests"
    fi
```

Or split into multiple repos with pipeline dependencies (advanced).

---

## 6. Lab — Day 6

1. Add Slack notify pipe on `main` (use webhook secret).
2. Enforce PR pipeline before merge to `main`.
3. Add secret scan pipe to PR workflow.
4. Pin all pipe versions in YAML.

---

## Quick reference

| Task | Approach |
|------|----------|
| Notify | `atlassian/slack-notify` pipe |
| PR CI | `pull-requests:` section |
| Pin versions | `pipe: name:1.2.3` |

**Prev:** [Day 5](../day5/) · **Next:** [Day 7 — Production Bitbucket Pipelines](../day7/)
