terraform {
  required_version = ">=1.11.0"
  required_providers {
    ct = {
      source  = "poseidon/ct"
      version = ">=0.13.0"
    }

    http = {
      source  = "hashicorp/http"
      version = ">=3.4.5"
    }

    local = {
      source  = "hashicorp/local"
      version = ">=2.5.2"
    }

    proxmox = {
      source  = "bpg/proxmox"
      version = ">=0.75.0"
    }

    random = {
      source  = "hashicorp/random"
      version = ">=3.7.1"
    }

    tls = {
      source  = "hashicorp/tls"
      version = ">=4.0.6"
    }
  }
}
