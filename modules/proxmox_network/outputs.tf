output "default_network" {
  description = "Default Linux Bridge interface"
  value       = proxmox_virtual_environment_network_linux_bridge.vmbr0
}

output "portainer_network" {
  description = "Linux Bridge interface for Portainer_network cluster"
  value       = proxmox_virtual_environment_network_linux_bridge.portainer_network
}
