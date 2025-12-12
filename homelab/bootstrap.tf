resource "tls_private_key" "root_key" {
  algorithm = "ED25519"
}

module "proxmox_network" {
  source                = "../modules/proxmox_network"
  proxmox_pve_node_name = var.proxmox_pve_node_name
  proxmox_pve_node_ip   = var.proxmox_pve_node_ip
}

module "proxmox_apt" {
  source                = "../modules/proxmox_apt"
  proxmox_pve_node_name = var.proxmox_pve_node_name
}

module "proxmox_pools" {
  source = "../modules/proxmox_pools"
}

module "proxmox_users" {
  source = "../modules/proxmox_users"
  users = [
    {
      username    = "operations-automation"
      role_id     = "Operations"
      pam_enabled = false
    },
  ]
}
