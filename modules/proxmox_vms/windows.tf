resource "proxmox_virtual_environment_download_file" "win11_enterprise_iso" {
  content_type = "iso"
  datastore_id = "local"
  overwrite    = false
  file_name    = "win11-enterprise.iso"
  node_name    = var.proxmox_pve_node_name
  url          = "https://software-static.download.prss.microsoft.com/dbazure/888969d5-f34g-4e03-ac9d-1f9786c66749/26100.1742.240906-0331.ge_release_svc_refresh_CLIENTENTERPRISEEVAL_OEMRET_x64FRE_en-us.iso"
}

resource "proxmox_virtual_environment_download_file" "virtio_win_iso" {
  content_type = "iso"
  datastore_id = "local"
  node_name    = var.proxmox_pve_node_name
  url          = "https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso"
}

# resource "proxmox_virtual_environment_vm" "crowdstrike_test" {
#   name            = "CrowdStrike"
#   node_name       = var.proxmox_pve_node_name
#   pool_id         = var.portainer_pool_id
#   tags            = ["win11"]
#   stop_on_destroy = true
#   machine         = "q35"
#   on_boot         = false
#   started         = false
#   // start ms-cxh:localonly

#   scsi_hardware = "virtio-scsi-pci"

#   operating_system {
#     type = "win11"
#   }

#   bios = "ovmf"

#   cpu {
#     cores = 4
#     type  = "x86-64-v2-AES"
#   }

#   agent {
#     enabled = true
#   }

#   memory {
#     dedicated = 1024 * 6
#   }

#   network_device {
#     bridge = var.default_network
#   }

#   #   cdrom {
#   #     file_id   = proxmox_virtual_environment_download_file.virtio_win_iso.id
#   #     interface = "ide2"
#   #   }

#   cdrom {
#     file_id   = proxmox_virtual_environment_download_file.win11_enterprise_iso.id
#     interface = "ide2"
#   }

#   disk {
#     datastore_id = "local-lvm"
#     interface    = "scsi0"
#     size         = 64
#     iothread     = true
#   }

#   efi_disk {
#     datastore_id      = "local-lvm"
#     type              = "4m"
#     pre_enrolled_keys = true
#   }

#   tpm_state {
#     version      = "v2.0"
#     datastore_id = "local-lvm"
#   }

#   lifecycle {
#     ignore_changes = all
#   }
# }
