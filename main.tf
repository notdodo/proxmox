terraform {
  required_version = ">= 1.0"
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = ">=0.74.1"
    }

    talos = {
      source  = "siderolabs/talos"
      version = ">=0.7.1"
    }

    random = {
      source  = "hashicorp/random"
      version = ">=3.7.1"
    }
  }
}

resource "random_password" "password" {
  length           = 16
  special          = true
  override_special = "!#$%&?"
}

provider "proxmox" {
  endpoint = "https://192.168.178.15:8006/"
  insecure = true
  username = var.automation_user
  password = var.automation_password
}

resource "proxmox_virtual_environment_role" "operations" {
  role_id = "Operations"

  privileges = [
    "Datastore.Allocate",
    "Datastore.AllocateSpace",
    "Datastore.AllocateTemplate",
    "Datastore.Audit",
    "Group.Allocate",
    "Mapping.Audit",
    "Mapping.Use",
    "Pool.Allocate",
    "Pool.Audit",
    "Realm.AllocateUser",
    "SDN.Allocate",
    "SDN.Audit", "SDN.Use",
    "Sys.Audit",
    "Sys.Console",
    "Sys.Modify",
    "Sys.Syslog",
    "User.Modify",
    "VM.Allocate",
    "VM.Audit",
    "VM.Backup",
    "VM.Clone",
    "VM.Config.CDROM",
    "VM.Config.CPU",
    "VM.Config.Cloudinit",
    "VM.Config.Disk",
    "VM.Config.HWType",
    "VM.Config.Memory",
    "VM.Config.Network",
    "VM.Config.Options",
    "VM.Console",
    "VM.Migrate",
    "VM.Monitor",
    "VM.PowerMgmt",
    "VM.Snapshot",
    "VM.Snapshot.Rollback",
  ]
}

resource "proxmox_virtual_environment_user" "operations_automation" {
  acl {
    path      = "/"
    propagate = true
    role_id   = proxmox_virtual_environment_role.operations.role_id
  }

  comment  = "Managed by ~Pulumi~ Terraform"
  password = random_password.password.result
  user_id  = var.automation_user
  groups   = []
}

resource "proxmox_virtual_environment_download_file" "talos_image" {
  content_type = "iso"
  datastore_id = "local"
  node_name    = var.proxmox_pve_node_name
  url          = "https://factory.talos.dev/image/376567988ad370138ad8b2698212367b8edcb69b5fd68c80be1f2ec7d603b4ba/${var.talos_version}/metal-amd64.iso"
  file_name    = "talos-${var.talos_version}-amd64.img"
}


resource "proxmox_virtual_environment_apt_standard_repository" "nosubscription_source" {
  handle = "no-subscription"
  node   = var.proxmox_pve_node_name
}

resource "proxmox_virtual_environment_apt_repository" "nosubscription_source_config" {
  enabled   = true
  file_path = proxmox_virtual_environment_apt_standard_repository.nosubscription_source.file_path
  index     = proxmox_virtual_environment_apt_standard_repository.nosubscription_source.index
  node      = proxmox_virtual_environment_apt_standard_repository.nosubscription_source.node
}

resource "proxmox_virtual_environment_apt_standard_repository" "enterprise_source" {
  handle = "enterprise"
  node   = var.proxmox_pve_node_name
}

resource "proxmox_virtual_environment_apt_repository" "enterprise_source_config" {
  enabled   = false
  file_path = proxmox_virtual_environment_apt_standard_repository.enterprise_source.file_path
  index     = proxmox_virtual_environment_apt_standard_repository.enterprise_source.index
  node      = proxmox_virtual_environment_apt_standard_repository.enterprise_source.node
}

resource "proxmox_virtual_environment_apt_standard_repository" "ceph_quincy_nosubscription_source" {
  handle = "ceph-quincy-no-subscription"
  node   = var.proxmox_pve_node_name
}

resource "proxmox_virtual_environment_apt_repository" "ceph_quincy_nosubscription_source_config" {
  enabled   = true
  file_path = proxmox_virtual_environment_apt_standard_repository.ceph_quincy_nosubscription_source.file_path
  index     = proxmox_virtual_environment_apt_standard_repository.ceph_quincy_nosubscription_source.index
  node      = proxmox_virtual_environment_apt_standard_repository.ceph_quincy_nosubscription_source.node
}


resource "proxmox_virtual_environment_apt_standard_repository" "ceph_quincy_enterprise_source" {
  handle = "ceph-quincy-enterprise"
  node   = var.proxmox_pve_node_name
}

resource "proxmox_virtual_environment_apt_repository" "ceph_quincy_enterprise_source_config" {
  enabled   = false
  file_path = proxmox_virtual_environment_apt_standard_repository.ceph_quincy_enterprise_source.file_path
  index     = proxmox_virtual_environment_apt_standard_repository.ceph_quincy_enterprise_source.index
  node      = proxmox_virtual_environment_apt_standard_repository.ceph_quincy_enterprise_source.node
}
