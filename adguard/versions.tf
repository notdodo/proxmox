terraform {
  backend "s3" {
    bucket = "notdodo-terraform"
    key    = "proxmox-adguard"
    region = "eu-west-1"
  }

  required_version = ">=1.11.0"

  required_providers {
    adguard = {
      source  = "gmichels/adguard"
      version = ">=1.6.2"
    }
  }
}
