output "bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.app.id
}

output "bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.app.arn
}

output "availability_zones" {
  description = "Available AZ names in the region"
  value       = data.aws_availability_zones.available.names
}

output "account_id" {
  description = "Current AWS account ID"
  value       = data.aws_caller_identity.current.account_id
}
