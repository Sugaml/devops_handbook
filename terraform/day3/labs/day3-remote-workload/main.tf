# After bootstrap apply, set bucket and table names below, then:
#   terraform init -migrate-state

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "REPLACE_WITH_STATE_BUCKET_NAME"
    key            = "day3/lab/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "REPLACE_WITH_LOCK_TABLE_NAME"
    encrypt        = true
  }
}

provider "aws" {
  region = var.region
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "workload" {
  bucket = "${var.project}-day3-workload-${data.aws_caller_identity.current.account_id}"

  tags = {
    Project = var.project
    Day     = "3"
  }
}

resource "aws_s3_bucket_public_access_block" "workload" {
  bucket = aws_s3_bucket.workload.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
