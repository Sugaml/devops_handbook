run "plan_succeeds" {
  command = plan

  variables {
    project     = "devops-handbook"
    environment = "test"
    region      = "us-east-1"
  }

  assert {
    condition     = aws_s3_bucket.app.bucket != ""
    error_message = "S3 bucket must be present in plan"
  }

  assert {
    condition     = length(var.project) > 0
    error_message = "project variable must be set"
  }
}
