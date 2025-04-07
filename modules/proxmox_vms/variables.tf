variable "proxmox_pve_node_name" {
  description = "Name of the ProxmoxVE node"
  type        = string
}

variable "root_private_key" {
  description = "IPv4 of the ProxmoxVE node"
  type        = string
}

variable "proxmox_pve_node_ip" {
  description = "SSH Private key for root user"
  type        = string
}

variable "default_network" {
  description = "Default network (vmbr0)"
  type        = string
}

variable "flatcar_network" {
  description = "Network interface for private comms for Flatcar"
  type        = string
}

variable "flatcar_pool_id" {
  description = "Flatcar PVE resource pool id"
  type        = string
}
