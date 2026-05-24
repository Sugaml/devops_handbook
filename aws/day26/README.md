# Day 26 — CodeBuild & CodePipeline

**Goal:** Build container/app artifacts with CodeBuild and wire a minimal pipeline from source to deploy.

**Time:** 6–8 hours

**Services:** CodeBuild, CodePipeline, S3, IAM

---

## 1. Artifact bucket

```bash
PIPELINE_BUCKET="handbook-pipeline-${ACCOUNT_ID}"
aws s3api create-bucket --bucket "$PIPELINE_BUCKET" --region us-east-1
```

---

## 2. CodeBuild project

`buildspec.yml`:

```yaml
version: 0.2
phases:
  pre_build:
    commands:
      - echo "Logging in to ECR"
      - aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
  build:
    commands:
      - docker build -t $IMAGE_TAG .
      - docker push $IMAGE_TAG
  post_build:
    commands:
      - printf '{"image":"%s"}' $IMAGE_TAG > imagedefinitions.json
artifacts:
  files: imagedefinitions.json
```

```bash
aws codebuild create-project \
  --name handbook-build \
  --source type=GITHUB,location=https://github.com/your/repo.git \
  --artifacts type=S3,location="$PIPELINE_BUCKET" \
  --environment type=LINUX_CONTAINER,image=aws/codebuild/standard:7.0,computeType=BUILD_GENERAL1_SMALL,privilegedMode=true \
  --service-role arn:aws:iam::ACCOUNT_ID:role/CodeBuildServiceRole
```

---

## 3. CodePipeline skeleton

```bash
aws codepipeline create-pipeline --cli-input-json file://pipeline.json
aws codepipeline start-pipeline-execution --name handbook-pipeline
aws codepipeline get-pipeline-state --name handbook-pipeline
```

Stages typical: Source → Build → Deploy (ECS/CodeDeploy/Lambda).

---

## 4. GitHub / OIDC (production)

Prefer **OIDC** over long-lived AWS keys in GitHub Actions:

```yaml
# Conceptual — not AWS CLI
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::ACCOUNT:role/GitHubDeployRole
```

---

## 5. Lab — Day 26

1. Create S3 bucket + IAM roles for CodeBuild.
2. Run standalone CodeBuild with inline `buildspec` (echo + zip artifact).
3. Optional: connect public sample repo and pipeline with manual approval stage.
4. Delete pipeline, project, bucket.

**Previous:** [Day 25](../day25/) · **Next:** [Day 27 — EKS](../day27/)
