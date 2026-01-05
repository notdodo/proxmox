variable "automation_password" {
  description = "ProxmoxVE PVE password for `automation_user`"
  type        = string
  sensitive   = true
}

variable "cf_api_token" {
  description = "Cloudflare API token for ACME configuration"
  type        = string
  sensitive   = true
}

variable "acme_email_address" {
  description = "Email address to use for ACME registration"
  type        = string
  sensitive   = true
}

# tflint-ignore: terraform_unused_declarations
variable "portainer_api_key" {
  description = "API Key for Portainer instance"
  type        = string
  sensitive   = true
}

variable "adguard_login_bcrypt" {
  description = "Bcrypt hash for AdGuard Home admin password (bootstrap config)"
  type        = string
  sensitive   = true
}

variable "adguard_password" {
  description = "AdGuard Home password for API access"
  type        = string
  sensitive   = true
}
