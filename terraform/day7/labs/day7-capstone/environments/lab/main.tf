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

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  account_id  = data.aws_caller_identity.current.account_id
  name_prefix = "${var.project}-${var.environment}"
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Day         = "7"
  }
}

module "network" {
  source = "../../modules/vpc"

  name_prefix         = local.name_prefix
  availability_zone   = data.aws_availability_zones.available.names[0]
  tags                = local.common_tags
}

module "assets" {
  source = "../../modules/s3-bucket"

  bucket_name = "${var.project}-${var.environment}-assets-${local.account_id}"
  tags        = merge(local.common_tags, { Purpose = "assets" })
}

module "app" {
  source = "../../modules/ec2-app"

  name_prefix       = local.name_prefix
  vpc_id            = module.network.vpc_id
  subnet_id         = module.network.public_subnet_id
  assets_bucket_arn = module.assets.bucket_arn
  instance_type     = var.instance_type
  tags              = local.common_tags
}
