terraform {
  required_version = ">=1.11.0"
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = ">=0.75.0"
    }
  }
}

resource "proxmox_virtual_environment_pool" "flatcar_pool" {
  comment = "Managed by ~Pulumi~ Terraform"
  pool_id = "flatcar"
}
