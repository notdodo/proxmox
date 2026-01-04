terraform {
  required_version = ">=1.11.0"
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = ">=3.2.4"
    }

    proxmox = {
      source  = "bpg/proxmox"
      version = ">=0.78.0"
    }

    random = {
      source  = "hashicorp/random"
      version = ">=3.7.2"
    }

    tls = {
      source  = "hashicorp/tls"
      version = ">=4.1.0"
    }
  }
}

moved {
  from = proxmox_virtual_environment_container.alpine_lxc_template
  to   = proxmox_virtual_environment_container.adguard_lxc_template
}

moved {
  from = proxmox_virtual_environment_download_file.latest_turnkey_core
  to   = proxmox_virtual_environment_download_file.latest_debian_standard
}

locals {
  adguard_bootstrap_primary_config = templatefile("${path.module}/templates/adguard-bootstrap.yaml.tftpl", {
    username        = var.adguard_admin_username
    password_bcrypt = var.adguard_login_bcrypt
    server_name     = var.adguard_primary_server_name
    cert_pem        = var.https_cert
    private_key_pem = var.https_private_key
  })
  adguard_bootstrap_secondary_config = templatefile("${path.module}/templates/adguard-bootstrap.yaml.tftpl", {
    username        = var.adguard_admin_username
    password_bcrypt = var.adguard_login_bcrypt
    server_name     = var.adguard_secondary_server_name
    cert_pem        = var.https_cert
    private_key_pem = var.https_private_key
  })
}

resource "proxmox_virtual_environment_download_file" "latest_debian_standard" {
  content_type = "vztmpl"
  datastore_id = "local"
  node_name    = var.proxmox_pve_node_name
  url          = "http://download.proxmox.com/images/system/debian-13-standard_13.1-2_amd64.tar.zst"
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

resource "proxmox_virtual_environment_container" "adguard_lxc_template" {
  description = "Managed by ~Pulumi~ Terraform; Debian 13 standard LXC template (SSH enabled)"
  node_name   = var.proxmox_pve_node_name
  tags        = ["lxc", "template"]
  vm_id       = 8000
  template    = true

  initialization {
    hostname = "adguard-template"
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
    template_file_id = proxmox_virtual_environment_download_file.latest_debian_standard.id
    type             = "debian"
  }
}

resource "proxmox_virtual_environment_container" "adguard_primary" {
  description = "AdGuardHome Primary"
  node_name   = var.proxmox_pve_node_name
  tags        = ["adguard", "lxc"]
  vm_id       = 500
  clone {
    vm_id = proxmox_virtual_environment_container.adguard_lxc_template.vm_id
  }

  initialization {
    hostname = "adguard"

    ip_config {
      ipv4 {
        address = "192.168.178.200/24"
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
    host = "192.168.178.200"
    # kics-scan ignore-line
    private_key = tls_private_key.adguard_ssh_key.private_key_openssh
  }

  provisioner "remote-exec" {
    inline = [
      "apt-get update",
      "apt-get install -y ca-certificates curl iproute2 tar",
      "curl -fsSL -o /tmp/AdGuardHome_linux_amd64.tar.gz https://static.adguard.com/adguardhome/release/AdGuardHome_linux_amd64.tar.gz",
      "tar -C /opt -xzf /tmp/AdGuardHome_linux_amd64.tar.gz",
    ]
  }

  provisioner "file" {
    content     = local.adguard_bootstrap_primary_config
    destination = "/opt/AdGuardHome/AdGuardHome.yaml"
  }

  provisioner "remote-exec" {
    inline = [
      "cd /opt/AdGuardHome",
      "./AdGuardHome -s install",
      "systemctl enable --now AdGuardHome",
    ]
  }
}

resource "null_resource" "wait_for_adguard_primary" {
  depends_on = [proxmox_virtual_environment_container.adguard_primary]

  provisioner "remote-exec" {
    connection {
      type = "ssh"
      user = "root"
      host = "192.168.178.200"
      # kics-scan ignore-line
      private_key = tls_private_key.adguard_ssh_key.private_key_openssh
      timeout     = "5m"
    }

    inline = [
      "echo 'Primary AdGuard is reachable via SSH.'"
    ]
  }
}

resource "proxmox_virtual_environment_container" "adguard_secondary" {
  description = "AdGuardHome Secondary/Test"
  node_name   = var.proxmox_pve_node_name
  tags        = ["adguard", "lxc"]
  vm_id       = 501
  clone {
    vm_id = proxmox_virtual_environment_container.adguard_lxc_template.vm_id
  }

  depends_on = [
    proxmox_virtual_environment_container.adguard_primary,
    null_resource.wait_for_adguard_primary
  ]

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

  provisioner "remote-exec" {
    inline = [
      "apt-get update",
      "apt-get install -y ca-certificates curl tar",
      "curl -fsSL -o /tmp/AdGuardHome_linux_amd64.tar.gz https://static.adguard.com/adguardhome/release/AdGuardHome_linux_amd64.tar.gz",
      "tar -C /opt -xzf /tmp/AdGuardHome_linux_amd64.tar.gz",
    ]
  }

  provisioner "file" {
    content     = local.adguard_bootstrap_secondary_config
    destination = "/opt/AdGuardHome/AdGuardHome.yaml"
  }

  provisioner "remote-exec" {
    inline = [
      "cd /opt/AdGuardHome",
      "./AdGuardHome -s install",
      "systemctl enable --now AdGuardHome",
    ]
  }
}

resource "null_resource" "adguard_update_primary" {
  triggers = {
    version = var.adguardhome_version
  }

  connection {
    type = "ssh"
    user = "root"
    host = "192.168.178.200"
    # kics-scan ignore-line
    private_key = tls_private_key.adguard_ssh_key.private_key_openssh
  }

  provisioner "remote-exec" {
    inline = [
      "curl -fsSL -o /tmp/AdGuardHome_linux_amd64.tar.gz https://static.adguard.com/adguardhome/release/AdGuardHome_linux_amd64.tar.gz",
      "tar -C /opt -xzf /tmp/AdGuardHome_linux_amd64.tar.gz",
      "systemctl restart AdGuardHome",
    ]
  }

  depends_on = [proxmox_virtual_environment_container.adguard_primary]
}

resource "null_resource" "adguard_update_secondary" {
  triggers = {
    version = var.adguardhome_version
  }

  connection {
    type = "ssh"
    user = "root"
    host = "192.168.178.201"
    # kics-scan ignore-line
    private_key = tls_private_key.adguard_ssh_key.private_key_openssh
  }

  provisioner "remote-exec" {
    inline = [
      "curl -fsSL -o /tmp/AdGuardHome_linux_amd64.tar.gz https://static.adguard.com/adguardhome/release/AdGuardHome_linux_amd64.tar.gz",
      "tar -C /opt -xzf /tmp/AdGuardHome_linux_amd64.tar.gz",
      "systemctl restart AdGuardHome",
    ]
  }

  depends_on = [proxmox_virtual_environment_container.adguard_secondary]
}
