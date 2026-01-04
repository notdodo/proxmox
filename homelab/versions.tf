terraform {
  backend "s3" {
    bucket = "notdodo-terraform"
    key    = "proxmox"
    region = "eu-west-1"
  }

  required_version = ">=1.11.0"

  required_providers {
    acme = {
      source  = "vancluever/acme"
      version = ">=2.32.0"
    }

    adguard = {
      source  = "gmichels/adguard"
      version = ">=1.6.2"
    }

    proxmox = {
      source  = "bpg/proxmox"
      version = ">=0.78.0"
    }

    tls = {
      source  = "hashicorp/tls"
      version = ">=4.1.0"
    }
  }
}
