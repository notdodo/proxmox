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

resource "local_file" "private_key" {
  content  = tls_private_key.flatcar_key.private_key_openssh
  filename = "flatcar_ssh_key.pem"
}

data "ct_config" "flatcar" {
  count = 3
  content = templatefile("${path.module}/flatcar.yml", {
    ssh_authorized_keys = tls_private_key.flatcar_key.public_key_openssh
    hostname            = count.index == 0 ? "main" : "worker${count.index}"
    address             = "192.168.178.10${count.index}"
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

  template      = true
  started       = false
  kvm_arguments = "-fw_cfg name=opt/org.flatcar-linux/config,file=/var/lib/vz/snippets/${proxmox_virtual_environment_file.ignition_file[0].file_name}"


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

  # TODO: can't use this due to "shrinking" https://github.com/bpg/terraform-provider-proxmox/issues/1351
  # switched to remote-exec
  # disk {
  #   datastore_id = "local-lvm"
  #   file_format  = "raw"
  #   file_id      = proxmox_virtual_environment_download_file.flatcar_img_latest.id
  #   interface    = "scsi0"
  # }

  initialization {
    datastore_id = "local-lvm"
    interface    = "ide2"
  }

  network_device {
    bridge = "vmbr0"
  }

  connection {
    type        = "ssh"
    user        = "root"
    private_key = var.root_private_key
    host        = var.proxmox_pve_node_ip
  }

  provisioner "remote-exec" {
    inline = [
      "qm disk import ${self.vm_id} /var/lib/vz/template/iso/${proxmox_virtual_environment_download_file.flatcar_img_latest.file_name} local-lvm",
      "qm set ${self.vm_id} -scsihw virtio-scsi-pci --scsi0 local-lvm:vm-${self.vm_id}-disk-0",
    ]
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
    bridge = "vmbr0"
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
    bridge = "vmbr0"
  }

  memory {
    dedicated = 1024 * 2
  }
}
