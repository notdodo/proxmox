resource "proxmox_virtual_environment_download_file" "ubuntu_cloud_img" {
  content_type = "iso"
  datastore_id = "local"
  node_name    = var.proxmox_pve_node_name
  url          = "https://cloud-images.ubuntu.com/oracular/current/oracular-server-cloudimg-amd64.img"
}

resource "tls_private_key" "portainer_vm_key" {
  algorithm = "ED25519"
}

resource "random_password" "ceph_dashboard" {
  length           = 20
  special          = true
  min_lower        = 1
  min_numeric      = 1
  min_special      = 1
  min_upper        = 1
  override_special = "!#$%?-_"
}

resource "proxmox_virtual_environment_file" "user_data_cloud_config" {
  count        = 3
  content_type = "snippets"
  datastore_id = "local"
  node_name    = var.proxmox_pve_node_name

  source_raw {
    data = templatefile("${path.module}/portainer-init.yml", {
      ssh_key     = indent(6, tls_private_key.portainer_vm_key.private_key_openssh)
      ssh_pub_key = indent(6, tls_private_key.portainer_vm_key.public_key_openssh)
      label       = count.index == 0 ? "bootstrap" : "not"
      # kics-scan ignore-line
      dashboard_password = random_password.ceph_dashboard.result
    })
    file_name = "portainer-init-${count.index + 1}.yml"
  }
}

resource "proxmox_virtual_environment_vm" "portainer_node" {
  count           = 3
  name            = "portainer-node-${count.index + 1}"
  node_name       = var.proxmox_pve_node_name
  pool_id         = var.portainer_pool_id
  vm_id           = "10${count.index}"
  tags            = ["debian", "portainer"]
  description     = "Portainer node"
  stop_on_destroy = true

  initialization {
    user_account {
      username = "core"
      keys     = [trimspace(tls_private_key.portainer_vm_key.public_key_openssh)]
    }

    ip_config {
      ipv4 {
        address = "192.168.178.10${count.index}/24"
        gateway = "192.168.178.1"
      }
    }

    ip_config {
      ipv4 {
        address = "10.0.100.${count.index + 1}/24"
        gateway = "10.0.100.1"
      }
    }

    vendor_data_file_id = proxmox_virtual_environment_file.user_data_cloud_config[count.index].id
  }

  cpu {
    cores = 2
    type  = "x86-64-v2-AES"
  }

  agent {
    enabled = true
  }

  memory {
    dedicated = 1024 * 2
  }

  network_device {
    bridge = var.default_network
  }

  network_device {
    bridge = var.portainer_network
  }

  disk {
    datastore_id = "local-lvm"
    file_id      = proxmox_virtual_environment_download_file.ubuntu_cloud_img.id
    interface    = "scsi0"
    discard      = "on"
    size         = 15
  }

  disk {
    datastore_id = "local-lvm"
    interface    = "scsi1"
    size         = 20
  }
}
