variable "region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "ami_id" {
  description = "AMI ID for the instance"
  type        = string
  default     = "ami-0c55b159cbfafe1f0"
}

variable "key_pair_name" {
  description = "SSH key pair name for instance access"
  type        = string
}

variable "casper_version" {
  description = "Casper Docker image version"
  type        = string
  default     = "latest"
}
