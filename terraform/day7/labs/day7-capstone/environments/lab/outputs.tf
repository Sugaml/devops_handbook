output "vpc_id" {
  value = module.network.vpc_id
}

output "assets_bucket" {
  value = module.assets.bucket_id
}

output "instance_id" {
  value = module.app.instance_id
}

output "public_ip" {
  value = module.app.public_ip
}

output "http_url" {
  value = "http://${module.app.public_ip}:8080"
}
