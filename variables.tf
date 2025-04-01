variable "automation_user" {
  description = "ProxmoxVE PVE user to use for authentication"
  type        = string
  default     = "operations-automation@pve"
}

variable "automation_password" {
  description = "ProxmoxVE PVE password for `automation_user`"
  type        = string
}

variable "proxmox_pve_node_name" {
  description = "Name of the ProxmoxVE node"
  type        = string
  default     = "mainprox"
}

# https://github.com/siderolabs/talos/releases
# https://www.talos.dev/v1.9/introduction/support-matrix/
variable "talos_version" {
  description = "Talos version to use"
  type        = string
  default     = "1.9.5"
  validation {
    condition     = can(regex("^\\d+(\\.\\d+)+", var.talos_version))
    error_message = "Must be a version number."
  }
}
