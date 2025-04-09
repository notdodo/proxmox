data "http" "flatcar_version" {
  #checkov:skip=CKV2_AWS_36:No parameters are sent
  url = "https://stable.release.flatcar-linux.net/amd64-usr/current/version.txt"
}

locals {
  flatcar_version = regex("FLATCAR_VERSION_ID=(\\d+\\.\\d+\\.\\d+)", data.http.flatcar_version.response_body)[0]
}

resource "tls_private_key" "flatcar_key" {
  algorithm = "ED25519"
}

data "ct_config" "flatcar" {
  count = 3
  content = templatefile("${path.module}/flatcar.yml", {
    ssh_authorized_keys = tls_private_key.flatcar_key.public_key_openssh
    hostname            = count.index == 0 ? "main" : "worker${count.index}"
    address             = "192.168.178.10${count.index}"
    private_address     = "10.0.100.${count.index}"
  })
  pretty_print = false
  strict       = true
}

resource "proxmox_virtual_environment_download_file" "flatcar_img_latest" {
  content_type            = "iso"
  datastore_id            = "local"
  node_name               = var.proxmox_pve_node_name
  url                     = "https://stable.release.flatcar-linux.net/amd64-usr/current/flatcar_production_qemu_image.img.bz2"
  file_name               = "flatcar-stable-${local.flatcar_version}-qemu-image.img"
  decompression_algorithm = "bz2"
  overwrite               = false # TODO: need to avoid every time re-downloading the image https://github.com/bpg/terraform-provider-proxmox/issues/1740
}

resource "proxmox_virtual_environment_file" "ignition_file" {
  count        = 3
  node_name    = var.proxmox_pve_node_name
  content_type = "snippets"
  datastore_id = "local"

  source_raw {
    data      = data.ct_config.flatcar[count.index].rendered
    file_name = count.index == 0 ? "flatcar-main.ign" : "flatcar-worker${count.index}.ign"
  }
}

resource "proxmox_virtual_environment_vm" "flatcar_template" {
  name        = "flatcar-template"
  node_name   = var.proxmox_pve_node_name
  pool_id     = var.flatcar_pool_id
  vm_id       = 9000
  tags        = ["docker", "flatcar", "template", ]
  description = "Template VM for Flatcar ${local.flatcar_version}, each cloned VM is configured with separate Ign files."

  template = true
  started  = false

  boot_order = ["scsi0", "ide2", "net0"]

  cpu {
    cores = 4
  }

  agent {
    enabled = true
  }

  memory {
    dedicated = 1024 * 2
  }

  disk {
    datastore_id = "local-lvm"
    file_format  = "raw"
    file_id      = proxmox_virtual_environment_download_file.flatcar_img_latest.id
    interface    = "scsi0"
    size         = 9
  }
}

resource "proxmox_virtual_environment_vm" "flatcar_cluster_main" {
  name          = "flatcar-main"
  node_name     = var.proxmox_pve_node_name
  tags          = ["flatcar", "docker", "main"]
  on_boot       = true
  description   = "Flatcar Cluster main"
  pool_id       = var.flatcar_pool_id
  kvm_arguments = "-fw_cfg name=opt/org.flatcar-linux/config,file=/var/lib/vz/snippets/${proxmox_virtual_environment_file.ignition_file[0].file_name}"

  clone {
    vm_id = proxmox_virtual_environment_vm.flatcar_template.id
  }

  agent {
    enabled = true
  }

  initialization {
    datastore_id = "local-lvm"
    interface    = "ide2"
  }

  network_device {
    bridge = var.default_network
  }

  network_device {
    bridge = var.flatcar_network
  }

  memory {
    dedicated = 1024 * 2
  }
}

resource "proxmox_virtual_environment_vm" "flatcar_cluster_workers" {
  count         = 2
  name          = "flatcar-worker${count.index + 1}"
  node_name     = var.proxmox_pve_node_name
  tags          = ["flatcar", "docker", "worker"]
  on_boot       = true
  pool_id       = var.flatcar_pool_id
  kvm_arguments = "-fw_cfg name=opt/org.flatcar-linux/config,file=/var/lib/vz/snippets/${proxmox_virtual_environment_file.ignition_file[count.index + 1].file_name}"
  description   = "Flatcar Cluster worker${count.index + 1}"

  agent {
    enabled = true
  }
  clone {
    vm_id = proxmox_virtual_environment_vm.flatcar_template.id
  }

  initialization {
    datastore_id = "local-lvm"
    interface    = "ide2"
  }

  network_device {
    bridge = var.default_network
  }

  network_device {
    bridge = var.flatcar_network
  }

  memory {
    dedicated = 1024 * 2
  }
}
