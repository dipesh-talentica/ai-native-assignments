output "ecr_repository_url" {
  value = aws_ecr_repository.app_repo.repository_url
  description = "ECR repository URL for Docker images"
}

output "smtp_secret_arn" {
  value = aws_secretsmanager_secret.smtp.arn
  description = "ARN of the SMTP credentials secret"
}

output "cloudwatch_log_group" {
  value = aws_cloudwatch_log_group.app_logs.name
  description = "CloudWatch log group name"
}

output "ec2_instance_id" {
  value = aws_instance.app.id
  description = "EC2 instance ID"
}

output "ebs_volume_id" {
  value = aws_ebs_volume.sqlite.id
  description = "EBS volume ID for SQLite DB"
}

output "security_group_id" {
  value = aws_security_group.app_sg.id
  description = "Security group ID"
}

output "iam_role_arn" {
  value = aws_iam_role.ec2_role.arn
  description = "IAM role ARN for EC2 instance"
}
