module "adguard_config" {
  source = "../modules/adguard_config"
  count  = var.enable_adguard_config ? 1 : 0

  adguard_username              = var.adguard_username
  adguard_password              = var.adguard_password
  adguard_primary_host          = var.adguard_primary_host
  adguard_secondary_host        = var.adguard_secondary_host
  adguard_scheme                = var.adguard_scheme
  adguard_tls_insecure          = var.adguard_tls_insecure
  adguard_primary_server_name   = var.adguard_primary_server_name
  adguard_secondary_server_name = var.adguard_secondary_server_name

  certificate_pem = acme_certificate.thedodo.certificate_pem
  private_key_pem = acme_certificate.thedodo.private_key_pem

  providers = {
    adguard.primary   = adguard.primary
    adguard.secondary = adguard.secondary
  }

  depends_on = [module.proxmox_containers]
}

provider "adguard" {
  alias    = "primary"
  host     = var.adguard_primary_host
  scheme   = var.adguard_scheme
  username = var.adguard_username
  password = var.adguard_password
  insecure = var.adguard_tls_insecure
}

provider "adguard" {
  alias    = "secondary"
  host     = var.adguard_secondary_host
  scheme   = var.adguard_scheme
  username = var.adguard_username
  password = var.adguard_password
  insecure = var.adguard_tls_insecure
}
