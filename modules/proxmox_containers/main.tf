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
  }
}

variable "proxmox_pve_node_name" {
  description = "Name of the ProxmoxVE node"
  type        = string
}

variable "default_network" {
  description = "Default network (vmbr0)"
  type        = string
}

resource "proxmox_virtual_environment_download_file" "latest_alpine" {
  content_type = "vztmpl"
  datastore_id = "local"
  node_name    = var.proxmox_pve_node_name
  url          = "http://download.proxmox.com/images/system/alpine-3.20-default_20240908_amd64.tar.xz"
}

resource "random_password" "adguard_container_password" {
  length           = 20
  special          = true
  min_lower        = 1
  min_numeric      = 1
  min_special      = 1
  min_upper        = 1
  override_special = "!#$%?-_"
}

resource "tls_private_key" "adguard_ssh_key" {
  algorithm = "ED25519"
}

resource "proxmox_virtual_environment_container" "adguard_home" {
  description = "Managed by ~Pulumi~ Terraform"
  node_name   = var.proxmox_pve_node_name
  tags        = ["lxc", "adguard"]
  vm_id       = 500

  initialization {
    hostname = "adguard"

    ip_config {
      ipv4 {
        address = "192.168.178.200/24"
        gateway = "192.168.178.1"
      }
    }

    user_account {
      keys = [
        trimspace(tls_private_key.adguard_ssh_key.public_key_openssh)
      ]
      password = random_password.adguard_container_password.result
    }
  }

  network_interface {
    name = "vmbr0"
  }

  disk {
    datastore_id = "local-lvm"
    size         = 2
  }

  operating_system {
    template_file_id = proxmox_virtual_environment_download_file.latest_alpine.id
    # Or you can use a volume ID, as obtained from a "pvesm list <storage>"
    # template_file_id = "local:vztmpl/jammy-server-cloudimg-amd64.tar.gz"
    type = "alpine"
  }
}
