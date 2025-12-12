variable "proxmox_pve_node_name" {
  description = "Name of the ProxmoxVE node"
  type        = string
}

variable "default_network" {
  description = "Default network (vmbr0)"
  type        = string
}

variable "portainer" {
  description = "Optional Portainer cluster configuration"
  type = object({
    pool_id            = string
    network            = string
    cloudinit_template = string
    nodes = map(object({
      lan_ip          = string
      lan_gateway     = string
      cluster_ip      = string
      cluster_gateway = string
      bootstrap       = bool
    }))
  })
  default = null
}

variable "vm_definitions" {
  description = "Map of general-purpose VM definitions keyed by identifier"
  type = map(object({
    name             = string
    pool_id          = string
    tags             = list(string)
    description      = optional(string)
    stop_on_destroy  = optional(bool, true)
    machine          = optional(string)
    on_boot          = optional(bool, true)
    started          = optional(bool, true)
    scsi_hardware    = optional(string)
    bios             = optional(string)
    os_type          = string
    cpu_cores        = number
    cpu_type         = optional(string)
    memory_mb        = number
    agent_enabled    = optional(bool, true)
    networks         = list(object({ bridge = string }))
    mount_virtio_iso = optional(bool, true)
    iso = object({
      url                = string
      file_name          = string
      id                 = optional(string) # optional logical key for reuse across VMs; defaults to file_name or URL hash
      interface          = optional(string, "ide2")
      checksum           = optional(string)
      checksum_algorithm = optional(string)
      datastore_id       = optional(string, "local")
      content_type       = optional(string, "iso")
    })
    virtio_iso = optional(object({
      url          = string
      id           = optional(string) # optional logical key for reuse across VMs; defaults to file_name or URL hash
      file_name    = optional(string, "virtio-win.iso")
      interface    = optional(string, "ide3")
      datastore_id = optional(string, "local")
      content_type = optional(string, "iso")
    }))
    disk = object({
      size_gb      = number
      datastore_id = optional(string, "local-lvm")
      interface    = optional(string, "scsi0")
      iothread     = optional(bool, true)
      cache        = optional(string)
      discard      = optional(string)
    })
    efi = optional(object({
      datastore_id      = optional(string, "local-lvm")
      type              = optional(string, "4m")
      pre_enrolled_keys = optional(bool, true)
    }))
    tpm_state = optional(object({
      datastore_id = optional(string, "local-lvm")
      version      = optional(string, "v2.0")
    }))
    lifecycle_ignore_changes = optional(bool, false)
  }))
  default = {}
}
