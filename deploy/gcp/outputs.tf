output "instance_id" {
  description = "ID of the created GCE instance"
  value       = google_compute_instance.casper_node.id
}

output "instance_external_ip" {
  description = "External IP address of the instance"
  value       = google_compute_instance.casper_node.network_interface[0].access_config[0].nat_ip
}

output "instance_name" {
  description = "Name of the created instance"
  value       = google_compute_instance.casper_node.name
}
