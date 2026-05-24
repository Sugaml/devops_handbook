variable "region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "common_tags" {
  type = map(string)
  default = {
    ManagedBy = "terraform"
    Day       = "5"
  }
}

variable "teams" {
  description = "Map of team name to config"
  type = map(object({
    role        = string
    expire_days = number
  }))
}

variable "enable_backup_bucket" {
  type    = bool
  default = true
}
