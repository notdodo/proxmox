terraform {
  required_version = ">=1.11.0"
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = ">=0.75.0"
    }

    random = {
      source  = "hashicorp/random"
      version = ">=3.7.1"
    }
  }
}

resource "random_password" "password" {
  count            = length(var.users)
  length           = 20
  special          = true
  min_lower        = 1
  min_numeric      = 1
  min_special      = 1
  min_upper        = 1
  override_special = "!#$%?-_"
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

resource "proxmox_virtual_environment_user" "users" {
  for_each = { for user in var.users : user.username => user }
  acl {
    path      = "/"
    propagate = true
    role_id   = each.value.role_id
  }

  comment = "Managed by ~Pulumi~ Terraform"
  # kics-scan ignore-line
  password = random_password.password[index(var.users, each.value)].result
  user_id  = each.value.pam_enabled ? "${each.value.username}@pam" : "${each.value.username}@pve"
  groups   = []
}
