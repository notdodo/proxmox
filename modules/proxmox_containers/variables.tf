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

variable "adguard_primary_config_template" {
  description = "Template content for the primary AdGuard instance"
  type        = string
}

variable "adguard_secondary_config_template" {
  description = "Template content for the secondary AdGuard instance"
  type        = string
}
