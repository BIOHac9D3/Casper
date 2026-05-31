terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

resource "aws_instance" "casper_node" {
  ami           = var.ami_id
  instance_type = var.instance_type
  key_name      = var.key_pair_name

  tags = {
    Name        = "Casper-Node-${var.environment}"
    Environment = var.environment
    Project     = "Casper"
  }
}
