terraform {
  required_version = ">=1.11.0"
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = ">=0.74.1"
    }
  }
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
