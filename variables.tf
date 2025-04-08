variable "automation_user" {
  description = "ProxmoxVE PVE user to use for authentication"
  type        = string
  default     = "operations-automation"
}

variable "automation_password" {
  description = "ProxmoxVE PVE password for `automation_user`"
  type        = string
}

variable "proxmox_pve_node_name" {
  description = "Name of the ProxmoxVE node"
  type        = string
  default     = "mainprox"
}

variable "proxmox_pve_node_ip" {
  description = "IPv4 of the ProxmoxVE node"
  type        = string
  default     = "192.168.178.15"
}

variable "proxmox_pve_node_domain" {
  description = "DNS of the ProxmoxVE node"
  type        = string
  default     = "proxmox.thedodo.xyz"
}

variable "proxmox_pve_node_port" {
  description = "Port of the ProxmoxVE node"
  type        = string
  default     = "8006"
}

variable "cf_api_token" {
  description = "Cloudflare API token for ACME configuration"
  type        = string
}

variable "acme_email_address" {
  description = "Email address to use for ACME registration"
  type        = string
}

variable "portainer_api_key" {
  description = "API Key for Portainer instance"
  type        = string
}

variable "adguard_login_bcrypt" {
  description = "Bcrypt hash for AdGuard Web GUI"
  type        = string
}
