terraform {
  required_version = ">=1.11.0"
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = ">=0.74.1"
    }

    random = {
      source  = "hashicorp/random"
      version = ">=3.7.1"
    }
  }
}

variable "proxmox_pve_node_name" {
  description = "Name of the ProxmoxVE node"
  type        = string
}

variable "default_network" {
  description = "Default network (vmbr0)"
  type        = string
}

resource "proxmox_virtual_environment_download_file" "latest_alpine" {
  content_type = "vztmpl"
  datastore_id = "local"
  node_name    = var.proxmox_pve_node_name
  url          = "http://download.proxmox.com/images/system/alpine-3.20-default_20240908_amd64.tar.xz"
}

resource "random_password" "adguard_container_password" {
  length           = 20
  special          = true
  min_lower        = 1
  min_numeric      = 1
  min_special      = 1
  min_upper        = 1
  override_special = "!#$%?-_"
}

resource "tls_private_key" "adguard_ssh_key" {
  algorithm = "ED25519"
}

resource "local_file" "adguard_ssh_key" {
  content  = tls_private_key.adguard_ssh_key.private_key_openssh
  filename = "./keys/adguard_ssh_key.pem"
}

resource "proxmox_virtual_environment_container" "adguard_home" {
  description = "Managed by ~Pulumi~ Terraform"
  node_name   = var.proxmox_pve_node_name
  tags        = ["lxc", "adguard"]
  vm_id       = 500

  initialization {
    hostname = "adguard"

    ip_config {
      ipv4 {
        address = "192.168.178.200/24"
        gateway = "192.168.178.1"
      }
    }

    user_account {
      keys = [
        trimspace(tls_private_key.adguard_ssh_key.public_key_openssh)
      ]
      # kics-scan ignore-line
      password = random_password.adguard_container_password.result
    }
  }

  network_interface {
    name = var.default_network
  }

  disk {
    datastore_id = "local-lvm"
    size         = 2
  }

  operating_system {
    template_file_id = proxmox_virtual_environment_download_file.latest_alpine.id
    # Or you can use a volume ID, as obtained from a "pvesm list <storage>"
    # template_file_id = "local:vztmpl/jammy-server-cloudimg-amd64.tar.gz"
    type = "alpine"
  }
}


resource "proxmox_virtual_environment_container" "alpine_lxc_template" {
  description = "Managed by ~Pulumi~ Terraform; to use this template you need to install openssh-server and enable the service<br/>`apk update; apk add openssh-server openssh`<br/>`rc-update add sshd default; service sshd start`"
  node_name   = var.proxmox_pve_node_name
  tags        = ["lxc", "template"]
  vm_id       = 8000
  template    = true

  initialization {
    hostname = "alpine-template"
    user_account {
      keys = [
        trimspace(tls_private_key.adguard_ssh_key.public_key_openssh)
      ]
      # kics-scan ignore-line
      password = random_password.adguard_container_password.result
    }
  }

  disk {
    datastore_id = "local-lvm"
    size         = 2
  }

  operating_system {
    template_file_id = proxmox_virtual_environment_download_file.latest_alpine.id
    type             = "alpine"
  }
}

resource "proxmox_virtual_environment_container" "adguard_test" {
  description = "AdGuardHome secondary/test"
  node_name   = var.proxmox_pve_node_name
  tags        = ["lxc", "adguard"]
  vm_id       = 501
  clone {
    vm_id = proxmox_virtual_environment_container.alpine_lxc_template.vm_id
  }

  initialization {
    hostname = "adguard2"

    ip_config {
      ipv4 {
        address = "192.168.178.201/24"
        gateway = "192.168.178.1"
      }
    }
  }

  network_interface {
    name = var.default_network
  }

  disk {
    datastore_id = "local-lvm"
    size         = 2
  }

  connection {
    type = "ssh"
    user = "root"
    host = "192.168.178.201"
    # kics-scan ignore-line
    private_key = tls_private_key.adguard_ssh_key.private_key_openssh
  }

  provisioner "file" {
    content = templatefile("${path.module}/AdGuardHome.yaml", {
      password = "${bcrypt(random_password.adguard_container_password.result, 2)}"
    })
    destination = "/tmp/AdGuardHome.yaml"
  }

  provisioner "remote-exec" {
    inline = [
      "apk update",
      "apk upgrade",
      "apk add adguardhome --repository=https://dl-cdn.alpinelinux.org/alpine/edge/testing",
      "rc-update add adguardhome default",
      "mv /tmp/AdGuardHome.yaml /var/lib/adguardhome/AdGuardHome.yaml",
      "service adguardhome start",
    ]
  }
}
