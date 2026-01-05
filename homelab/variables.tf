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

# variable "portainer_api_key" {
#   description = "API Key for Portainer instance"
#   type        = string
# }

variable "adguard_login_bcrypt" {
  description = "Bcrypt hash for AdGuard Home admin password (bootstrap config)"
  type        = string
}

variable "adguard_username" {
  description = "AdGuard Home username for API access"
  type        = string
}

variable "adguard_password" {
  description = "AdGuard Home password for API access"
  type        = string
  sensitive   = true
}

variable "adguard_primary_host" {
  description = "Host (and optional port) for the primary AdGuard Home instance"
  type        = string
  default     = "192.168.178.200:3000"
}

variable "adguard_secondary_host" {
  description = "Host (and optional port) for the secondary AdGuard Home instance"
  type        = string
  default     = "192.168.178.201:3000"
}

variable "adguard_scheme" {
  description = "Scheme to use for the AdGuard Home API"
  type        = string
  default     = "http"
}

variable "adguard_primary_server_name" {
  description = "TLS server name for the primary AdGuard Home instance"
  type        = string
  default     = "adguard.thedodo.xyz"
}

variable "adguard_secondary_server_name" {
  description = "TLS server name for the secondary AdGuard Home instance"
  type        = string
  default     = "adguard2.thedodo.xyz"
}

variable "adguard_tls_insecure" {
  description = "Whether to skip TLS certificate validation when calling the AdGuard Home API"
  type        = bool
  default     = true
}

variable "enable_adguard_config" {
  description = "Whether to apply AdGuard Home configuration via the provider"
  type        = bool
  default     = false
}

variable "adguardhome_version" {
  description = "AdGuard Home version trigger for updates (change to force update)"
  type        = string
  default     = "latest"
}
