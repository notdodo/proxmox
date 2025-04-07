terraform {
  required_version = ">=1.11.0"
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = ">=0.74.1"
    }

    random = {
      source  = "hashicorp/random"
      version = ">=3.7.1"
    }

    ct = {
      source  = "poseidon/ct"
      version = ">=0.13.0"
    }
  }
}
