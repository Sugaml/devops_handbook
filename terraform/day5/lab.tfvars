region      = "us-east-1"
project     = "devops-handbook"
environment = "lab"

teams = {
  platform = {
    role        = "platform-ops"
    expire_days = 0
  }
  data = {
    role        = "analytics"
    expire_days = 90
  }
  frontend = {
    role        = "web"
    expire_days = 30
  }
}

enable_backup_bucket = true
