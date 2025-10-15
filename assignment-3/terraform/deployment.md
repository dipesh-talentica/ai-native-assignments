# Deployment Guide: CI/CD Dashboard on AWS with Terraform

## Prerequisites
- AWS account with permissions for EC2, ECR, IAM, CloudWatch, Secrets Manager
- Terraform installed
- Docker installed (for building/pushing images)
- AWS CLI installed and configured

## Steps

### 1. Initialize Terraform
```sh
cd assignment-3/terraform
terraform init
```

### 2. Review and Apply Infrastructure
```sh
terraform plan
terraform apply
```

### 3. Build and Push Docker Image to ECR
- Get ECR repo URL from Terraform output
- Authenticate and push:
```sh
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker build -t ci-cd-dashboard ../..
docker tag ci-cd-dashboard:latest <ecr-repo-url>:latest
docker push <ecr-repo-url>:latest
```

### 4. SSH into EC2 and Run Container
- Get EC2 public IP and SSH command from Terraform output
- SSH in:
```sh
ssh -i ~/.ssh/example-ssh-key.pem ec2-user@<public-ip>
```
- Pull and run the container (replace `<ecr-repo-url>`):
```sh
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker pull <ecr-repo-url>:latest
docker run -d -p 80:80 --env-file /data/.env -v /data:/app/data <ecr-repo-url>:latest
```

### 5. Access the Dashboard
- Open `http://<public-ip>` in your browser

## Notes
- SMTP/email secrets are stored in AWS Secrets Manager (dummy values)
- SQLite DB is stored on EBS volume at `/data`
- CloudWatch logging is enabled
- Security group allows HTTP (80) and SSH (22)

## Troubleshooting
- If the dashboard is not accessible:
	- Check EC2 instance status in AWS Console
	- Ensure security group allows inbound HTTP (80) and SSH (22)
	- Confirm public IP is correct and instance is running
- To view EC2 logs:
	- Go to CloudWatch > Log Groups > `/ci-cd-dashboard/app`
	- Check for errors in startup or Docker logs
- To verify EBS volume:
	- SSH into EC2 and run `df -h` to confirm `/data` is mounted
- To check Docker container:
	- Run `docker ps` to see running containers
	- Run `docker logs <container-id>` for logs
- To check environment variables:
	- Inspect `/data/.env` for correct SMTP/email values

## Teardown / Destroy Resources
To remove all provisioned resources and avoid ongoing costs:
```sh
terraform destroy
```
This will delete EC2, EBS, security group, IAM roles, ECR repo, CloudWatch log group, and Secrets Manager secrets.

## AI Tools Used
- GitHub Copilot for generating Terraform scripts, deployment guide, and documentation

## Folder Structure
- Terraform scripts: `assignment-3/terraform/`
- App code: `backend/`, `frontend/`
