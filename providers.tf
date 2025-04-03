terraform {
  required_version = ">=1.11.0"
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = ">=2.5.2"
    }

    proxmox = {
      source  = "bpg/proxmox"
      version = ">=0.74.1"
    }

    tls = {
      source  = "hashicorp/tls"
      version = ">=4.0.6"
    }
  }
}

provider "proxmox" {
  endpoint = "https://${var.proxmox_pve_node_domain}:${var.proxmox_pve_node_port}/"
  insecure = false
  username = strcontains(var.automation_user, "@p") ? var.automation_user : "${var.automation_user}@pve"
  password = var.automation_password

  ssh {
    agent       = true
    username    = "root"
    private_key = file("./root_node_ssh_key.pem")
  }
}
