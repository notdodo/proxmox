terraform {
  required_version = ">=1.11.0"
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = ">=2.5.2"
    }

    null = {
      source  = "hashicorp/null"
      version = ">=3.2.3"
    }

    proxmox = {
      source  = "bpg/proxmox"
      version = ">=0.75.0"
    }

    random = {
      source  = "hashicorp/random"
      version = ">=3.7.1"
    }

    template = {
      source  = "hashicorp/template"
      version = "2.2.0"
    }

    tls = {
      source  = "hashicorp/tls"
      version = ">=4.0.6"
    }
  }
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

data "template_file" "adguard_primary" {
  template = file("${path.module}/AdGuardHome.yaml")
  vars = {
    # kics-scan ignore-line
    password        = var.adguard_login_bcrypt
    hostname        = "adguard"
    cert_pem        = var.https_cert
    private_key_pem = var.https_private_key
  }
}

data "template_file" "adguard_secondary" {
  template = file("${path.module}/AdGuardHome-test.yaml")
  vars = {
    # kics-scan ignore-line
    password        = var.adguard_login_bcrypt
    hostname        = "adguard2"
    cert_pem        = var.https_cert
    private_key_pem = var.https_private_key
  }
}

resource "null_resource" "adguard_template_change_primary" {
  triggers = {
    rendered_template_sha = sha256(data.template_file.adguard_primary.rendered)
  }
}

resource "null_resource" "adguard_template_change_secondary" {
  triggers = {
    rendered_template_sha = sha256(data.template_file.adguard_secondary.rendered)
  }
}

resource "proxmox_virtual_environment_container" "adguard_primary" {
  description = "AdGuardHome Primary"
  node_name   = var.proxmox_pve_node_name
  tags        = ["adguard", "lxc"]
  vm_id       = 500
  clone {
    vm_id = proxmox_virtual_environment_container.alpine_lxc_template.vm_id
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

  provisioner "file" {
    content     = data.template_file.adguard_primary.rendered
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

  lifecycle {
    replace_triggered_by = [null_resource.adguard_template_change_primary]
  }
}

resource "null_resource" "wait_for_adguard_primary" {
  depends_on = [proxmox_virtual_environment_container.adguard_primary]

  provisioner "remote-exec" {
    connection {
      type        = "ssh"
      user        = "root"
      host        = "192.168.178.200"
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
    vm_id = proxmox_virtual_environment_container.alpine_lxc_template.vm_id
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

  provisioner "file" {
    content     = data.template_file.adguard_secondary.rendered
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

  lifecycle {
    replace_triggered_by = [null_resource.adguard_template_change_secondary]
  }
}
