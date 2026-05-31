output "instance_id" {
  description = "ID of the created EC2 instance"
  value       = aws_instance.casper_node.id
}

output "instance_public_ip" {
  description = "Public IP address of the instance"
  value       = aws_instance.casper_node.public_ip
}

output "instance_public_dns" {
  description = "Public DNS name of the instance"
  value       = aws_instance.casper_node.public_dns
}
