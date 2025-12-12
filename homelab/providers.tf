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

provider "acme" {
  server_url = local.acme_directory
}
