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
  account_suffix = data.aws_caller_identity.current.account_id
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Day         = "4"
  }
}

module "logs" {
  source = "./modules/s3-bucket"

  bucket_name       = "${var.project}-logs-${local.account_suffix}"
  enable_versioning = true
  tags              = merge(local.common_tags, { Purpose = "logs" })
}

module "assets" {
  source = "./modules/s3-bucket"

  bucket_name       = "${var.project}-assets-${local.account_suffix}"
  enable_versioning = false
  tags              = merge(local.common_tags, { Purpose = "assets" })
}
