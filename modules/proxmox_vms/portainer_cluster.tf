locals {
  portainer_nodes = {
    portainer-node-1 = {
      lan_ip          = "192.168.178.100/24"
      lan_gateway     = "192.168.178.1"
      cluster_ip      = "10.0.100.1/24"
      cluster_gateway = "10.0.100.1"
      bootstrap       = true
    }
    portainer-node-2 = {
      lan_ip          = "192.168.178.101/24"
      lan_gateway     = "192.168.178.1"
      cluster_ip      = "10.0.100.2/24"
      cluster_gateway = "10.0.100.1"
      bootstrap       = false
    }
    portainer-node-3 = {
      lan_ip          = "192.168.178.102/24"
      lan_gateway     = "192.168.178.1"
      cluster_ip      = "10.0.100.3/24"
      cluster_gateway = "10.0.100.1"
      bootstrap       = false
    }
  }
}

resource "proxmox_virtual_environment_download_file" "ubuntu_cloud_img" {
  content_type       = "iso"
  datastore_id       = "local"
  node_name          = var.proxmox_pve_node_name
  url                = "https://cloud-images.ubuntu.com/releases/oracular/release/ubuntu-24.10-server-cloudimg-amd64.img"
  checksum           = "69f31d3208895e5f646e345fbc95190e5e311ecd1359a4d6ee2c0b6483ceca03"
  checksum_algorithm = "sha256"
}

resource "tls_private_key" "portainer_vm_key" {
  algorithm = "ED25519"
}

resource "proxmox_virtual_environment_file" "user_data_cloud_config" {
  for_each     = local.portainer_nodes
  content_type = "snippets"
  datastore_id = "local"
  node_name    = var.proxmox_pve_node_name

  source_raw {
    data = templatefile("${path.module}/portainer-init.yml", {
      ssh_key     = indent(6, tls_private_key.portainer_vm_key.private_key_openssh)
      ssh_pub_key = indent(6, tls_private_key.portainer_vm_key.public_key_openssh)
      label       = each.value.bootstrap ? "bootstrap" : "not"
    })
    file_name = "init-${each.key}.yml"
  }
}

resource "proxmox_virtual_environment_hardware_mapping_dir" "portainer_share" {
  name = "portainer_share"

  map = [{
    node = var.proxmox_pve_node_name
    path = "/mnt/portainer_share"
  }]
}

# resource "proxmox_virtual_environment_vm" "portainer_node" {
#   for_each        = local.portainer_nodes
#   name            = each.key
#   node_name       = var.proxmox_pve_node_name
#   pool_id         = var.portainer_pool_id
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
#     bridge = var.portainer_network
#   }

#   disk {
#     datastore_id = "local-lvm"
#     file_id      = proxmox_virtual_environment_download_file.ubuntu_cloud_img.id
#     interface    = "scsi0"
#     size         = 20
#     cache        = "writeback"
#     discard      = "on"
#   }

#   virtiofs {
#     mapping = proxmox_virtual_environment_hardware_mapping_dir.portainer_share.name
#   }

# }
