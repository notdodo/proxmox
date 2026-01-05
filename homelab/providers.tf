locals {
  automation_user         = "root@pam"
  proxmox_pve_node_domain = "proxmox.thedodo.xyz"
  proxmox_pve_node_port   = "8006"
}

provider "proxmox" {
  endpoint = "https://${local.proxmox_pve_node_domain}:${local.proxmox_pve_node_port}/"
  insecure = false
  username = strcontains(local.automation_user, "@p") ? local.automation_user : "${local.automation_user}@pve"
  password = var.automation_password

  ssh {
    agent    = true
    username = "root"
  }
}

provider "acme" {
  server_url = local.acme_directory
}
