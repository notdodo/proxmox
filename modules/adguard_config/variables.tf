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
