output "bucket_map" {
  description = "Team name to bucket ID"
  value = {
    for team, bucket in aws_s3_bucket.team : team => bucket.id
  }
}

output "backup_bucket" {
  value = var.enable_backup_bucket ? aws_s3_bucket.backup[0].id : null
}
