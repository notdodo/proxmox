locals {
  vm_networks = {
    for name, vm in var.vm_definitions :
    name => length(vm.networks) > 0 ? vm.networks : [{ bridge = var.default_network }]
  }
  vm_ignore_all           = { for name, vm in var.vm_definitions : name => vm if try(vm.lifecycle_ignore_changes, false) }
  vm_manage_changes       = { for name, vm in var.vm_definitions : name => vm if !try(vm.lifecycle_ignore_changes, false) }
  vm_iso_key              = { for name, vm in var.vm_definitions : name => coalesce(try(vm.iso.id, null), vm.iso.file_name, sha1(vm.iso.url)) }
  vm_iso_interface        = { for name, vm in var.vm_definitions : name => lookup(vm.iso, "interface", "ide2") }
  vm_virtio_iso_key       = { for name, vm in var.vm_definitions : name => try(coalesce(vm.virtio_iso.id, vm.virtio_iso.file_name, sha1(vm.virtio_iso.url)), null) }
  vm_virtio_iso_interface = { for name, vm in var.vm_definitions : name => try(lookup(vm.virtio_iso, "interface", "ide3"), null) }
  iso_sources             = { for name, vm in var.vm_definitions : coalesce(try(vm.iso.id, null), vm.iso.file_name, sha1(vm.iso.url)) => vm.iso }
  virtio_iso_sources      = { for name, vm in var.vm_definitions : coalesce(vm.virtio_iso.id, vm.virtio_iso.file_name, sha1(vm.virtio_iso.url)) => vm.virtio_iso if try(vm.virtio_iso, null) != null }
}

resource "proxmox_virtual_environment_download_file" "vm_iso" {
  for_each = local.iso_sources

  content_type       = lookup(each.value, "content_type", "iso")
  datastore_id       = lookup(each.value, "datastore_id", "local")
  file_name          = each.value.file_name
  node_name          = var.proxmox_pve_node_name
  url                = each.value.url
  checksum           = try(each.value.checksum, null)
  checksum_algorithm = try(each.value.checksum_algorithm, null)
}

resource "proxmox_virtual_environment_download_file" "vm_virtio_iso" {
  for_each = local.virtio_iso_sources

  content_type = lookup(each.value, "content_type", "iso")
  datastore_id = lookup(each.value, "datastore_id", "local")
  file_name    = lookup(each.value, "file_name", "virtio-win.iso")
  node_name    = var.proxmox_pve_node_name
  url          = each.value.url
}

resource "proxmox_virtual_environment_vm" "vm" {
  for_each        = local.vm_manage_changes
  name            = each.value.name
  node_name       = var.proxmox_pve_node_name
  pool_id         = each.value.pool_id
  tags            = each.value.tags
  description     = try(each.value.description, null)
  stop_on_destroy = try(each.value.stop_on_destroy, true)
  machine         = try(each.value.machine, null)
  on_boot         = try(each.value.on_boot, true)
  started         = try(each.value.started, true)
  scsi_hardware   = try(each.value.scsi_hardware, null)
  bios            = try(each.value.bios, null)

  operating_system {
    type = each.value.os_type
  }

  cpu {
    cores = each.value.cpu_cores
    type  = try(each.value.cpu_type, null)
  }

  agent {
    enabled = try(each.value.agent_enabled, true)
  }

  memory {
    dedicated = each.value.memory_mb
  }

  dynamic "network_device" {
    for_each = local.vm_networks[each.key]
    content {
      bridge = network_device.value.bridge
    }
  }

  cdrom {
    file_id   = proxmox_virtual_environment_download_file.vm_iso[local.vm_iso_key[each.key]].id
    interface = local.vm_iso_interface[each.key]
  }

  dynamic "disk" {
    for_each = (try(each.value.mount_virtio_iso, true) && local.vm_virtio_iso_key[each.key] != null && contains(keys(proxmox_virtual_environment_download_file.vm_virtio_iso), local.vm_virtio_iso_key[each.key])) ? [1] : []
    content {
      datastore_id = lookup(each.value.virtio_iso, "datastore_id", "local")
      interface    = coalesce(local.vm_virtio_iso_interface[each.key], "ide3")
      file_id      = proxmox_virtual_environment_download_file.vm_virtio_iso[local.vm_virtio_iso_key[each.key]].id
      file_format  = "raw"
      size         = 1
    }
  }

  disk {
    datastore_id = lookup(each.value.disk, "datastore_id", "local-lvm")
    interface    = lookup(each.value.disk, "interface", "scsi0")
    size         = each.value.disk.size_gb
    iothread     = lookup(each.value.disk, "iothread", true)
    cache        = try(each.value.disk.cache, null)
    discard      = try(each.value.disk.discard, null)
  }

  dynamic "efi_disk" {
    for_each = try(each.value.efi, null) == null ? [] : [each.value.efi]
    content {
      datastore_id      = lookup(efi_disk.value, "datastore_id", "local-lvm")
      type              = lookup(efi_disk.value, "type", "4m")
      pre_enrolled_keys = lookup(efi_disk.value, "pre_enrolled_keys", true)
    }
  }

  dynamic "tpm_state" {
    for_each = try(each.value.tpm_state, null) == null ? [] : [each.value.tpm_state]
    content {
      version      = lookup(tpm_state.value, "version", "v2.0")
      datastore_id = lookup(tpm_state.value, "datastore_id", "local-lvm")
    }
  }

  lifecycle {}
}

resource "proxmox_virtual_environment_vm" "vm_ignore_changes" {
  for_each        = local.vm_ignore_all
  name            = each.value.name
  node_name       = var.proxmox_pve_node_name
  pool_id         = each.value.pool_id
  tags            = each.value.tags
  description     = try(each.value.description, null)
  stop_on_destroy = try(each.value.stop_on_destroy, true)
  machine         = try(each.value.machine, null)
  on_boot         = try(each.value.on_boot, true)
  started         = try(each.value.started, true)
  scsi_hardware   = try(each.value.scsi_hardware, null)
  bios            = try(each.value.bios, null)

  operating_system {
    type = each.value.os_type
  }

  cpu {
    cores = each.value.cpu_cores
    type  = try(each.value.cpu_type, null)
  }

  agent {
    enabled = try(each.value.agent_enabled, true)
  }

  memory {
    dedicated = each.value.memory_mb
  }

  dynamic "network_device" {
    for_each = local.vm_networks[each.key]
    content {
      bridge = network_device.value.bridge
    }
  }

  cdrom {
    file_id   = proxmox_virtual_environment_download_file.vm_iso[local.vm_iso_key[each.key]].id
    interface = local.vm_iso_interface[each.key]
  }

  dynamic "disk" {
    for_each = (try(each.value.mount_virtio_iso, true) && local.vm_virtio_iso_key[each.key] != null && contains(keys(proxmox_virtual_environment_download_file.vm_virtio_iso), local.vm_virtio_iso_key[each.key])) ? [1] : []
    content {
      datastore_id = lookup(each.value.virtio_iso, "datastore_id", "local")
      interface    = coalesce(local.vm_virtio_iso_interface[each.key], "ide3")
      file_id      = proxmox_virtual_environment_download_file.vm_virtio_iso[local.vm_virtio_iso_key[each.key]].id
      file_format  = "raw"
      size         = 1
    }
  }

  disk {
    datastore_id = lookup(each.value.disk, "datastore_id", "local-lvm")
    interface    = lookup(each.value.disk, "interface", "scsi0")
    size         = each.value.disk.size_gb
    iothread     = lookup(each.value.disk, "iothread", true)
    cache        = try(each.value.disk.cache, null)
    discard      = try(each.value.disk.discard, null)
  }

  dynamic "efi_disk" {
    for_each = try(each.value.efi, null) == null ? [] : [each.value.efi]
    content {
      datastore_id      = lookup(efi_disk.value, "datastore_id", "local-lvm")
      type              = lookup(efi_disk.value, "type", "4m")
      pre_enrolled_keys = lookup(efi_disk.value, "pre_enrolled_keys", true)
    }
  }

  dynamic "tpm_state" {
    for_each = try(each.value.tpm_state, null) == null ? [] : [each.value.tpm_state]
    content {
      version      = lookup(tpm_state.value, "version", "v2.0")
      datastore_id = lookup(tpm_state.value, "datastore_id", "local-lvm")
    }
  }

  lifecycle {
    ignore_changes = all
  }
}
