locals {
  portainer_config = {
    pool_id            = module.proxmox_pools.portainer_pool.id
    network            = module.proxmox_network.portainer_network.name
    nodes              = local.portainer_nodes
    cloudinit_template = abspath("${path.root}/../files/templates/portainer-init.yml")
  }

  vm_definitions = {
    generic_win11 = {
      name             = "Win11"
      pool_id          = module.proxmox_pools.portainer_pool.id
      tags             = ["win11"]
      description      = "Generic Win11 Evaluation"
      stop_on_destroy  = true
      machine          = "q35"
      on_boot          = false
      started          = false
      scsi_hardware    = "virtio-scsi-pci"
      bios             = "ovmf"
      os_type          = "win11"
      cpu_cores        = 4
      cpu_type         = "x86-64-v2-AES"
      memory_mb        = 1024 * 6
      agent_enabled    = true
      mount_virtio_iso = true
      networks = [{
        bridge = module.proxmox_network.default_network.name
      }]
      iso = {
        url          = "https://software-static.download.prss.microsoft.com/dbazure/888969d5-f34g-4e03-ac9d-1f9786c66749/26100.1742.240906-0331.ge_release_svc_refresh_CLIENTENTERPRISEEVAL_OEMRET_x64FRE_en-us.iso"
        file_name    = "win11-enterprise.iso"
        interface    = "ide2"
        datastore_id = "local"
      }
      virtio_iso = {
        url          = "https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso"
        file_name    = "virtio-win.iso"
        datastore_id = "local"
      }
      disk = {
        size_gb      = 64
        datastore_id = "local-lvm"
        interface    = "scsi0"
      }
      efi = {
        datastore_id      = "local-lvm"
        type              = "4m"
        pre_enrolled_keys = true
      }
      tpm_state = {
        datastore_id = "local-lvm"
        version      = "v2.0"
      }
      lifecycle_ignore_changes = true
    }
  }
}

module "proxmox_vms" {
  source                = "../modules/proxmox_vms"
  proxmox_pve_node_name = var.proxmox_pve_node_name
  default_network       = module.proxmox_network.default_network.name
  portainer             = local.portainer_config
  vm_definitions        = local.vm_definitions
}

module "proxmox_containers" {
  source                = "../modules/proxmox_containers"
  proxmox_pve_node_name = var.proxmox_pve_node_name
  default_network       = module.proxmox_network.default_network.name
  # kics-scan ignore-line
  https_private_key                 = acme_certificate.thedodo.private_key_pem
  https_cert                        = acme_certificate.thedodo.certificate_pem
  adguard_login_bcrypt              = var.adguard_login_bcrypt
  adguard_primary_config_template   = file(abspath("${path.root}/../files/templates/AdGuardHome.yaml"))
  adguard_secondary_config_template = file(abspath("${path.root}/../files/templates/AdGuardHome-test.yaml"))
}

# module "portainer" {
#   source            = "../modules/portainer"
#   portainer_api_key = var.portainer_api_key
#   # kics-scan ignore-line
#   https_private_key = acme_certificate.thedodo.private_key_pem
#   https_cert        = acme_certificate.thedodo.certificate_pem
# }
