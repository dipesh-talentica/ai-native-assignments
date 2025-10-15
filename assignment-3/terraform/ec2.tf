data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnet_ids" "default" {
  vpc_id = data.aws_vpc.default.id
}

resource "aws_security_group" "app_sg" {
  name        = "ci-cd-dashboard-sg"
  description = "Allow HTTP and SSH"
  vpc_id      = data.aws_vpc.default.id
  tags = {
    Name        = "ci-cd-dashboard-sg"
    Project     = "CI-CD-Dashboard"
    Environment = "Demo"
    Owner       = "DevOps"
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_role" "ec2_role" {
  name = "ci-cd-dashboard-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecr_pull" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "cw_logs" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_role_policy_attachment" "secrets_manager" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "ci-cd-dashboard-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

resource "aws_ebs_volume" "sqlite" {
  availability_zone = data.aws_subnet_ids.default.ids[0] != null ? data.aws_subnet_ids.default.ids[0] : "us-east-1a"
  size              = var.ebs_volume_size
  type              = "gp3"
  tags = {
    Name        = "ci-cd-dashboard-db"
    Project     = "CI-CD-Dashboard"
    Environment = "Demo"
    Owner       = "DevOps"
  }
}

resource "aws_instance" "app" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.instance_type
  subnet_id                   = data.aws_subnet_ids.default.ids[0]
  vpc_security_group_ids      = [aws_security_group.app_sg.id]
  key_name                    = var.ssh_key_name
  iam_instance_profile        = aws_iam_instance_profile.ec2_profile.name

  root_block_device {
    volume_size = 16
    volume_type = "gp3"
  }

  tags = {
    Name        = "ci-cd-dashboard-app"
    Project     = "CI-CD-Dashboard"
    Environment = "Demo"
    Owner       = "DevOps"
  }

  user_data = <<-EOF
#!/bin/bash
# Install Docker
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
# Attach EBS volume
sudo mkfs -t xfs /dev/xvdf
sudo mkdir -p /data
sudo mount /dev/xvdf /data
sudo chown ec2-user:ec2-user /data
# Install jq for JSON parsing
sudo yum install -y jq
# Fetch SMTP/email secrets from Secrets Manager
aws secretsmanager get-secret-value --secret-id smtp_credentials --region us-east-1 | jq -r .SecretString > /data/smtp.json
# Create .env file from secrets
cat <<EOT > /data/.env
SMTP_HOST=$(jq -r .host /data/smtp.json)
SMTP_PORT=$(jq -r .port /data/smtp.json)
SMTP_USER=$(jq -r .username /data/smtp.json)
SMTP_PASS=$(jq -r .password /data/smtp.json)
EMAIL_FROM=$(jq -r .from /data/smtp.json)
EOT
# Authenticate to ECR and pull image (placeholder URI)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker pull 123456789012.dkr.ecr.us-east-1.amazonaws.com/ci-cd-dashboard:latest
# Run container with env and volume
docker run -d -p 80:80 --env-file /data/.env -v /data:/app/data 123456789012.dkr.ecr.us-east-1.amazonaws.com/ci-cd-dashboard:latest
EOF

  depends_on = [aws_ebs_volume.sqlite]
}

resource "aws_volume_attachment" "db_attach" {
  device_name = "/dev/xvdf"
  volume_id   = aws_ebs_volume.sqlite.id
  instance_id = aws_instance.app.id
  force_detach = true
}

output "ec2_public_ip" {
  value = aws_instance.app.public_ip
  description = "Public IP of the EC2 instance"
}

output "ssh_command" {
  value = "ssh -i ~/.ssh/example-ssh-key.pem ec2-user@${aws_instance.app.public_ip}"
  description = "SSH command to connect to EC2"
}
