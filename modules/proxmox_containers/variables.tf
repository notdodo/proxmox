variable "proxmox_pve_node_name" {
  description = "Name of the ProxmoxVE node"
  type        = string
}

variable "default_network" {
  description = "Default network (vmbr0)"
  type        = string
}

variable "https_private_key" {
  description = "Private Key PEM for HTTPS certificate"
  type        = string
}

variable "https_cert" {
  description = "HTTPS Public certificate"
  type        = string
}

variable "adguard_login_bcrypt" {
  description = "Bcrypt hash for AdGuard Web GUI"
  type        = string
}
