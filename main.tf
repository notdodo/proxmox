provider "acme" {
  server_url = "https://acme-v02.api.letsencrypt.org/directory"
}

resource "acme_registration" "registration" {
  email_address = var.acme_email_address
}

resource "acme_certificate" "thedodo" {
  account_key_pem = acme_registration.registration.account_key_pem
  common_name     = "*.thedodo.xyz"

  dns_challenge {
    provider = "cloudflare"

    config = {
      CF_DNS_API_TOKEN = var.cf_api_token
    }
  }
}

module "proxmox_vms" {
  source                = "./modules/proxmox_vms"
  proxmox_pve_node_name = var.proxmox_pve_node_name
  default_network       = module.proxmox_network.default_network.name
  flatcar_pool_id       = module.proxmox_pools.flatcar_pool.id
  flatcar_network       = module.proxmox_network.flatcar_network.name
}

module "proxmox_containers" {
  source                = "./modules/proxmox_containers"
  proxmox_pve_node_name = var.proxmox_pve_node_name
  default_network       = module.proxmox_network.default_network.name
  # kics-scan ignore-line
  https_private_key    = acme_certificate.thedodo.private_key_pem
  https_cert           = acme_certificate.thedodo.certificate_pem
  adguard_login_bcrypt = var.adguard_login_bcrypt
}

module "portainer" {
  source            = "./modules/portainer"
  portainer_api_key = var.portainer_api_key
  # kics-scan ignore-line
  https_private_key = acme_certificate.thedodo.private_key_pem
  https_cert        = acme_certificate.thedodo.certificate_pem
}
