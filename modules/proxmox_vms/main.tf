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

variable "proxmox_pve_node_name" {
  description = "Name of the ProxmoxVE node"
  type        = string
}

variable "root_private_key" {
  description = "IPv4 of the ProxmoxVE node"
  type        = string
}

variable "proxmox_pve_node_ip" {
  description = "SSH Private key for root user"
  type        = string
}

variable "flatcar_pool_id" {
  description = "Flatcar PVE resource pool id"
  type        = string
}
