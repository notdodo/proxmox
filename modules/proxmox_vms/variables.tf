variable "proxmox_pve_node_name" {
  description = "Name of the ProxmoxVE node"
  type        = string
}

variable "default_network" {
  description = "Default network (vmbr0)"
  type        = string
}

variable "portainer_network" {
  description = "Network interface for private comms for Portainer"
  type        = string
}

variable "portainer_pool_id" {
  description = "Portainer PVE resource pool id"
  type        = string
}
