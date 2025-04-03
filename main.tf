module "proxmox_vms" {
  source                = "./modules/proxmox_vms"
  proxmox_pve_node_name = var.proxmox_pve_node_name
  proxmox_pve_node_ip   = var.proxmox_pve_node_ip
  flatcar_pool_id       = module.proxmox_pools.flatcar_pool.id
  # kics-scan ignore-line
  root_private_key = tls_private_key.root_key.private_key_openssh
}
