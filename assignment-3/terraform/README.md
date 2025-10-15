
# AI-Native KRA – DevOps Assignment 3 (IaC + Cloud Deployment)

## Goal
Take your CI/CD Pipeline Health Dashboard (Assignment 2) and deploy it to the cloud using Infrastructure-as-Code (IaC).

You will use AI-native tools (ChatGPT, Copilot, Cursor) to help generate, debug, and document your IaC scripts.

# Terraform AWS Deployment for CI/CD Dashboard
## Assignment Tasks & Requirements

- **Provision Infrastructure with IaC**
  - Use Terraform to create:
    - A VM/Compute instance (EC2, GCP VM, or Azure VM)
    - Networking basics (VPC + Security Group/Firewall)
    - A managed DB (if your app needs one, e.g., RDS/Postgres/CloudSQL)
- **Deploy Your App**
  - Use Terraform to install Docker and deploy your containerized app (from Assignment 2)
  - App should be accessible via a public URL/IP
- **AI-Native Workflow**
  - Use AI tools (ChatGPT, Copilot, Cursor) for:
    - Generating Terraform code
    - Writing deployment scripts
    - Creating documentation

## Expected Outcome
- A live dashboard running on cloud (AWS/GCP/Azure)
- Infrastructure fully provisioned with Terraform (not manual clicks)
- Documentation showing how AI tools were used

## Deliverables
- Terraform Scripts – committed to GitHub repo (`/infra` folder)
- Deployment Guide (`deployment.md`)
- How to apply Terraform & deploy app
- AI prompts/examples used
- Prompt Logs – record of prompts used (`prompts.md`)
## AI-Native Workflow
All Terraform scripts, deployment guides, and documentation in this project were generated using AI-native tools (GitHub Copilot, ChatGPT, Cursor) as required by the assignment.

This configuration deploys the demo app to AWS EC2 with Docker, ECR, EBS, CloudWatch, and Secrets Manager.


## Steps

1. **Initialize Terraform**
   ```sh
   terraform init
   ```
2. **Review and apply the plan**
   ```sh
   terraform plan
   terraform apply
   ```
3. **Build and push Docker image to ECR**
   - Use the ECR repo URL from outputs
   - Example:
     ```sh
     aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
     docker build -t ci-cd-dashboard ../..
     docker tag ci-cd-dashboard:latest <ecr-repo-url>:latest
     docker push <ecr-repo-url>:latest
     ```
4. **Automated container startup**
   - EC2 instance will automatically pull SMTP/email secrets from Secrets Manager, create a .env file, pull the ECR image, and run the container after provisioning.
   - No manual SSH or container run needed unless troubleshooting.

## Accessing the Dashboard
- Open `http://<ec2-public-ip>` in your browser (see Terraform output for IP)

## Outputs
- EC2 public IP and SSH command
- ECR repository URL
- SMTP secret ARN
- CloudWatch log group name
- EC2 instance ID
- EBS volume ID
- Security group ID
- IAM role ARN

## Notes
- SMTP/email secrets are stored in AWS Secrets Manager (dummy values)
- SQLite DB is stored on an attached EBS volume at `/data`
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
