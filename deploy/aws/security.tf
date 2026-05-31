resource "aws_security_group" "casper_sg" {
  name        = "casper-node-sg-${var.environment}"
  description = "Security group for Casper Node"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "Casper-Node-SG-${var.environment}"
    Environment = var.environment
    Project     = "Casper"
  }
}
