variable "bucket_name" {
  type        = string
  description = "Globally unique S3 bucket name"
}

variable "enable_versioning" {
  type    = bool
  default = true
}

variable "enable_encryption" {
  type    = bool
  default = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
