variable "adguard_server_name" {
  description = "TLS server name for the AdGuard Home instance"
  type        = string
}

variable "blocked_services" {
  description = "Blocked services to enable in AdGuard Home"
  type        = set(string)
}

variable "filter_lists" {
  description = "Filter lists to configure in AdGuard Home"
  type = map(object({
    enabled = bool
    url     = string
  }))
}

variable "user_rules" {
  description = "Custom user rules to configure in AdGuard Home"
  type        = list(string)
}

variable "certificate_pem" {
  description = "HTTPS Public certificate"
  type        = string
}

variable "private_key_pem" {
  description = "Private Key PEM for HTTPS certificate"
  type        = string
}
