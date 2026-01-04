variable "proxmox_pve_node_name" {
  description = "Name of the ProxmoxVE node"
  type        = string
}

variable "default_network" {
  description = "Default network (vmbr0)"
  type        = string
}

variable "adguard_admin_username" {
  description = "AdGuard Home admin username for bootstrap configuration"
  type        = string
}

variable "adguard_login_bcrypt" {
  description = "Bcrypt hash for AdGuard Home admin password (bootstrap config)"
  type        = string
}

variable "adguard_primary_server_name" {
  description = "TLS server name for the primary AdGuard Home instance"
  type        = string
}

variable "adguard_secondary_server_name" {
  description = "TLS server name for the secondary AdGuard Home instance"
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

variable "adguardhome_version" {
  description = "AdGuard Home version trigger for updates (change to force update)"
  type        = string
  default     = "latest"
}
