output "state_bucket_name" {
  value = aws_s3_bucket.terraform_state.id
}

output "state_bucket_arn" {
  value = aws_s3_bucket.terraform_state.arn
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.terraform_lock.name
}

output "backend_config_snippet" {
  description = "Paste into workload backend.tf (replace placeholders)"
  value = <<-EOT
    terraform {
      backend "s3" {
        bucket         = "${aws_s3_bucket.terraform_state.id}"
        key            = "ENV/PROJECT/terraform.tfstate"
        region         = "${var.region}"
        dynamodb_table = "${aws_dynamodb_table.terraform_lock.name}"
        encrypt        = true
      }
    }
  EOT
}
