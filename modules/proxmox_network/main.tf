terraform {
  required_version = ">=1.11.0"
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = ">=0.74.1"
    }
  }
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

resource "proxmox_virtual_environment_network_linux_bridge" "flatcar_network" {
  node_name = var.proxmox_pve_node_name
  name      = "vmbr100"

  address   = "10.0.100.0/24"
  autostart = true
  comment   = "Managed by ~Pulumi~ Terraform; dedicated to internal LAN for Flatcar cluster"
}
