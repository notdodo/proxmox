locals {
  portainer_enabled = var.portainer != null
}

resource "proxmox_virtual_environment_download_file" "ubuntu_cloud_img" {
  count              = local.portainer_enabled ? 1 : 0
  content_type       = "iso"
  datastore_id       = "local"
  node_name          = var.proxmox_pve_node_name
  url                = "https://cloud-images.ubuntu.com/releases/server/25.10/release/ubuntu-25.10-server-cloudimg-amd64.img"
  checksum           = "0b883af8dd5975c4311e0e24554a6caec2fa68eafc2eae44e9ff592c6ab821bb"
  checksum_algorithm = "sha256"
}

resource "tls_private_key" "portainer_vm_key" {
  count     = local.portainer_enabled ? 1 : 0
  algorithm = "ED25519"
}

resource "proxmox_virtual_environment_file" "user_data_cloud_config" {
  for_each     = local.portainer_enabled ? var.portainer.nodes : {}
  content_type = "snippets"
  datastore_id = "local"
  node_name    = var.proxmox_pve_node_name

  source_raw {
    data = templatefile(var.portainer.cloudinit_template, {
      ssh_key     = indent(6, tls_private_key.portainer_vm_key[0].private_key_openssh)
      ssh_pub_key = indent(6, tls_private_key.portainer_vm_key[0].public_key_openssh)
      label       = each.value.bootstrap ? "bootstrap" : "not"
    })
    file_name = "init-${each.key}.yml"
  }
}

resource "proxmox_virtual_environment_hardware_mapping_dir" "portainer_share" {
  count = local.portainer_enabled ? 1 : 0
  name  = "portainer_share"

  map = [{
    node = var.proxmox_pve_node_name
    path = "/mnt/portainer_share"
  }]
}

# resource "proxmox_virtual_environment_vm" "portainer_node" {
#   for_each        = var.portainer_nodes
#   name            = each.key
#   node_name       = var.proxmox_pve_node_name
#   pool_id         = var.portainer.pool_id
#   tags            = ["portainer", "ubuntu"]
#   description     = "${each.key} - Portainer Node"
#   stop_on_destroy = true

#   initialization {
#     user_account {
#       username = "core"
#       keys     = [trimspace(tls_private_key.portainer_vm_key.public_key_openssh)]
#     }

#     ip_config {
#       ipv4 {
#         address = each.value.lan_ip
#         gateway = each.value.lan_gateway
#       }
#     }

#     ip_config {
#       ipv4 {
#         address = each.value.cluster_ip
#         gateway = each.value.cluster_gateway
#       }
#     }

#     vendor_data_file_id = proxmox_virtual_environment_file.user_data_cloud_config[each.key].id
#   }

#   cpu {
#     cores = 2
#     type  = "x86-64-v3"
#   }

#   agent {
#     enabled = true
#   }

#   memory {
#     dedicated = 1024 * 4
#   }

#   network_device {
#     bridge = var.default_network
#   }

#   network_device {
#     bridge = var.portainer.network
#   }

#   disk {
#     datastore_id = "local-lvm"
#     file_id      = proxmox_virtual_environment_download_file.ubuntu_cloud_img[0].id
#     interface    = "scsi0"
#     size         = 20
#     cache        = "writeback"
#     discard      = "on"
#   }

#   virtiofs {
#     mapping = proxmox_virtual_environment_hardware_mapping_dir.portainer_share[0].name
#   }

# }
