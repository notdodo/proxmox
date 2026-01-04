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
}

variable "adguard_secondary_host" {
  description = "Host (and optional port) for the secondary AdGuard Home instance"
  type        = string
}

variable "adguard_scheme" {
  description = "Scheme to use for the AdGuard Home API"
  type        = string
}

variable "adguard_tls_insecure" {
  description = "Whether to skip TLS certificate validation when calling the AdGuard Home API"
  type        = bool
}

variable "adguard_primary_server_name" {
  description = "TLS server name for the primary AdGuard Home instance"
  type        = string
}

variable "adguard_secondary_server_name" {
  description = "TLS server name for the secondary AdGuard Home instance"
  type        = string
}

variable "certificate_pem" {
  description = "HTTPS Public certificate"
  type        = string
}

variable "private_key_pem" {
  description = "Private Key PEM for HTTPS certificate"
  type        = string
}
