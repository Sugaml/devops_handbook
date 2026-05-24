variable "name_prefix" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "assets_bucket_arn" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
