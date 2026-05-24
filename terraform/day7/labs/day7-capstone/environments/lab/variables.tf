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

variable "instance_type" {
  type    = string
  default = "t3.micro"
}
