variable "proxmox_pve_node_name" {
  description = "Name of the ProxmoxVE node"
  type        = string
}

variable "users" {
  description = "List of Users with roles"
  type = list(object(
    {
      username    = string
      role_id     = string
      pam_enabled = bool
    }
  ))
}
