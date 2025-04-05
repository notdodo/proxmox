output "default_network" {
  value = proxmox_virtual_environment_network_linux_bridge.vmbr0
}

output "flatcar_network" {
  value = proxmox_virtual_environment_network_linux_bridge.flatcar_network
}
