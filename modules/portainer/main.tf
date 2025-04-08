terraform {
  required_version = ">=1.11.0"
  required_providers {
    portainer = {
      source  = "grulicht/portainer"
      version = ">=1.0.2"
    }
  }
}

provider "portainer" {
  endpoint        = var.portainer_instance
  api_key         = var.portainer_api_key
  skip_ssl_verify = true
}

resource "portainer_ssl" "cert_update" {
  cert         = var.https_cert
  key          = var.https_private_key
  http_enabled = false
}
