terraform {
  required_version = ">=1.11.0"
  required_providers {
    ct = {
      source  = "poseidon/ct"
      version = ">=0.13.0"
    }

    http = {
      source  = "hashicorp/http"
      version = ">=3.5.0"
    }

    proxmox = {
      source  = "bpg/proxmox"
      version = ">=0.78.0"
    }

    random = {
      source  = "hashicorp/random"
      version = ">=3.7.2"
    }

    tls = {
      source  = "hashicorp/tls"
      version = ">=4.1.0"
    }
  }
}
