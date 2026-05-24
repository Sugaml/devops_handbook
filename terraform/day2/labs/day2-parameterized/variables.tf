variable "region" {
  type        = string
  description = "AWS region"
  default     = "us-east-1"
}

variable "project" {
  type        = string
  description = "Project name for naming and tags"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,18}[a-z0-9]$", var.project))
    error_message = "project must be 3-20 chars: lowercase letters, numbers, hyphens; start with letter."
  }
}

variable "environment" {
  type        = string
  description = "Environment label"

  validation {
    condition     = contains(["lab", "dev", "staging", "prod"], var.environment)
    error_message = "environment must be lab, dev, staging, or prod."
  }
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into common_tags"
  default     = {}
}

variable "enable_versioning" {
  type        = bool
  description = "Enable S3 versioning"
  default     = true
}

variable "enable_encryption" {
  type        = bool
  description = "Enable default bucket encryption"
  default     = true
}
