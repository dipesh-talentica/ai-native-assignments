variable "ssh_key_name" {
  description = "Name of the SSH key pair to use for EC2 access"
  type        = string
  default     = "example-ssh-key"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "ebs_volume_size" {
  description = "Size of EBS volume for SQLite DB (GB)"
  type        = number
  default     = 8
}
