variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region to deploy to"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone to deploy to"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "machine_type" {
  description = "GCE machine type"
  type        = string
  default     = "e2-medium"
}

variable "image_family" {
  description = "Boot disk image family"
  type        = string
  default     = "debian-11"
}

variable "casper_version" {
  description = "Casper Docker image version"
  type        = string
  default     = "latest"
}
