output "default_network" {
  description = "Default network for Linux Bridge (vmbr0)"
  value       = proxmox_virtual_environment_network_linux_bridge.vmbr0
}

output "flatcar_network" {
  description = "Dedicated Linux Bridge for Flatcar"
  value       = proxmox_virtual_environment_network_linux_bridge.flatcar_network
}
