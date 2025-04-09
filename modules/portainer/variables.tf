variable "portainer_instance" {
  description = "URL of the Portainer instance"
  type        = string
  default     = "https://portainer.thedodo.xyz:9443"

}

variable "portainer_api_key" {
  description = "API Key for Portainer instance"
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
