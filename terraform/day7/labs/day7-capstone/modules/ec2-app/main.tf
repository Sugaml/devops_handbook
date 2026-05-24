data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_security_group" "app" {
  name        = "${var.name_prefix}-app-sg"
  description = "Allow HTTP from lab networks"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP from anywhere (lab only)"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-app-sg" })
}

resource "aws_iam_role" "app" {
  name = "${var.name_prefix}-app-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "s3_read" {
  name = "${var.name_prefix}-s3-read"
  role = aws_iam_role.app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:ListBucket"]
      Resource = [var.assets_bucket_arn, "${var.assets_bucket_arn}/*"]
    }]
  })
}

resource "aws_iam_instance_profile" "app" {
  name = "${var.name_prefix}-app-profile"
  role = aws_iam_role.app.name
}

resource "aws_instance" "app" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.app.id]
  iam_instance_profile   = aws_iam_instance_profile.app.name

  user_data = <<-EOF
              #!/bin/bash
              dnf install -y python3
              echo "DevOps Handbook Day 7 Capstone" > /tmp/index.html
              nohup python3 -m http.server 8080 --directory /tmp > /var/log/handbook-http.log 2>&1 &
              EOF

  user_data_replace_on_change = true

  tags = merge(var.tags, { Name = "${var.name_prefix}-app" })
}
