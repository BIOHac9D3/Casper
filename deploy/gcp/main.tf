terraform {
  required_version = ">= 1.0.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

resource "google_compute_instance" "casper_node" {
  name         = "casper-node-${var.environment}"
  machine_type = var.machine_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = var.image_family
    }
  }

  network_interface {
    network = "default"
    access_config {
    }
  }

  metadata = {
    startup-script = "docker run -d -p 8000:8000 ghcr.io/biohac9d3/casper:${var.casper_version}"
  }

  tags = ["casper", "${var.environment}"]
}
