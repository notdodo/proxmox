resource "tls_private_key" "root_key" {
  algorithm = "ED25519"
}

resource "local_file" "root_private_key" {
  content  = tls_private_key.root_key.private_key_openssh
  filename = "root_node_ssh_key.pem"
}

module "proxmox_network" {
  source                = "./modules/proxmox_network"
  proxmox_pve_node_name = var.proxmox_pve_node_name
  proxmox_pve_node_ip   = var.proxmox_pve_node_ip
}

module "proxmox_apt" {
  source                = "./modules/proxmox_apt"
  proxmox_pve_node_name = var.proxmox_pve_node_name
}

module "proxmox_pools" {
  source = "./modules/proxmox_pools"
}

module "proxmox_users" {
  source                = "./modules/proxmox_users"
  proxmox_pve_node_name = var.proxmox_pve_node_name
  users = [
    {
      username    = "operations-automation"
      role_id     = "Operations"
      pam_enabled = false
    },
    # {
    #   username    = "notdodo"
    #   role_id     = "Administrator"
    #   pam_enabled = true
    # }
  ]
}

resource "proxmox_virtual_environment_acme_account" "default" {
  name      = "default"
  contact   = "edoardo.rosa90+proxmox-acme@gmail.com"
  directory = "https://acme-v02.api.letsencrypt.org/directory"
  tos       = "https://letsencrypt.org/documents/LE-SA-v1.5-February-24-2025.pdf"
}

resource "proxmox_virtual_environment_acme_dns_plugin" "cloudflare_dns" {
  plugin           = "cloudflare-dns"
  api              = "cf"
  validation_delay = 0

  data = {
    CF_Account_ID = "938405242b51a1caf73f0b661bfb3dc2"
    CF_Zone_ID    = "cec5bf01afed114303a536c264a1f394"
  }

  lifecycle {
    # `data` manually managed
    ignore_changes = [data]
  }
}
