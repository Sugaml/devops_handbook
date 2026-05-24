output "bucket_name" {
  description = "Name of the lab S3 bucket"
  value       = aws_s3_bucket.lab.id
}

output "bucket_arn" {
  description = "ARN of the lab S3 bucket"
  value       = aws_s3_bucket.lab.arn
}

output "account_id" {
  description = "AWS account ID used in bucket naming"
  value       = data.aws_caller_identity.current.account_id
}
