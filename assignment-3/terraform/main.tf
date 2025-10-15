terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
  required_version = ">= 1.3.0"
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_ecr_repository" "app_repo" {
  name = "ci-cd-dashboard"
}

resource "aws_secretsmanager_secret" "smtp" {
  name = "smtp_credentials"
}

resource "aws_secretsmanager_secret_version" "smtp_value" {
  secret_id     = aws_secretsmanager_secret.smtp.id
  secret_string = jsonencode({
    host     = "smtp.example.com"
    port     = "587"
    username = "user@example.com"
    password = "dummy-password"
    from     = "noreply@example.com"
  })
}

resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/ci-cd-dashboard/app"
  retention_in_days = 7
}
