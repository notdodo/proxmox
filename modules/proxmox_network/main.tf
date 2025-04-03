terraform {
  required_version = ">=1.11.0"
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = ">=0.74.1"
    }
  }
}

variable "proxmox_pve_node_name" {
  description = "Name of the ProxmoxVE node"
  type        = string
}

variable "proxmox_pve_node_ip" {
  description = "IPv4 of the ProxmoxVE node"
  type        = string
}

resource "proxmox_virtual_environment_network_linux_bridge" "vmbr0" {
  node_name = var.proxmox_pve_node_name
  name      = "vmbr0"

  address   = "${var.proxmox_pve_node_ip}/24"
  gateway   = "192.168.178.1"
  autostart = true
  comment   = "Managed by ~Pulumi~ Terraform"

  ports = [
    # Network (or VLAN) interfaces to attach to the bridge, specified by their interface name
    "enp44s0"
  ]
}
