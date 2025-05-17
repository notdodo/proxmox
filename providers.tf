terraform {
  backend "s3" {
    bucket = "notdodo-terraform"
    key    = "proxmox"
    region = "eu-west-1"
  }

  required_version = ">=1.11.0"
  required_providers {

    acme = {
      source  = "vancluever/acme"
      version = ">=2.32.0"
    }

    proxmox = {
      source  = "bpg/proxmox"
      version = ">=0.78.0"
    }

    tls = {
      source  = "hashicorp/tls"
      version = ">=4.1.0"
    }
  }
}

provider "proxmox" {
  endpoint = "https://${var.proxmox_pve_node_domain}:${var.proxmox_pve_node_port}/"
  insecure = false
  username = strcontains(var.automation_user, "@p") ? var.automation_user : "${var.automation_user}@pve"
  password = var.automation_password

  ssh {
    agent    = true
    username = "root"
  }
}
