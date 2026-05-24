variable "region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project name used in resource names and tags"
  type        = string
  default     = "devops-handbook"
}

variable "environment" {
  description = "Environment label (lab, dev, staging, prod)"
  type        = string
  default     = "lab"
}
