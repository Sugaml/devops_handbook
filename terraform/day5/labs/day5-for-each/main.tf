terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
}

resource "aws_s3_bucket" "team" {
  for_each = var.teams

  bucket = "${var.project}-${each.key}-${local.account_id}"

  tags = merge(var.common_tags, {
    Team = each.key
    Role = each.value.role
  })

  lifecycle {
    precondition {
      condition     = can(regex("^[a-z][a-z0-9-]*$", each.key))
      error_message = "Team keys must start with a letter and contain only lowercase letters, numbers, hyphens."
    }
  }
}

resource "aws_s3_bucket_public_access_block" "team" {
  for_each = aws_s3_bucket.team

  bucket = each.value.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "team" {
  for_each = {
    for name, cfg in var.teams : name => cfg
    if cfg.expire_days > 0
  }

  bucket = aws_s3_bucket.team[each.key].id

  rule {
    id     = "expire-${each.key}"
    status = "Enabled"

    filter {}

    expiration {
      days = each.value.expire_days
    }
  }
}

resource "aws_s3_bucket" "backup" {
  count  = var.enable_backup_bucket ? 1 : 0
  bucket = "${var.project}-backup-${local.account_id}"

  tags = merge(var.common_tags, { Purpose = "backup" })
}
