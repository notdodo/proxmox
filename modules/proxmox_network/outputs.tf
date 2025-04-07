output "default_network" {
  description = "Default Linux Bridge interface"
  value       = proxmox_virtual_environment_network_linux_bridge.vmbr0
}

output "flatcar_network" {
  description = "Linux Bridge interface for Flatcar cluster"
  value       = proxmox_virtual_environment_network_linux_bridge.flatcar_network
}
