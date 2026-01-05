locals {
  acme_directory = "https://acme-v02.api.letsencrypt.org/directory"
  acme_tos_url   = "https://letsencrypt.org/documents/LE-SA-v1.5-February-24-2025.pdf"
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

resource "proxmox_virtual_environment_acme_account" "default" {
  name      = "default"
  contact   = var.acme_email_address
  directory = local.acme_directory
  tos       = local.acme_tos_url
}

resource "proxmox_virtual_environment_acme_dns_plugin" "cloudflare_dns" {
  plugin           = "cloudflare-dns"
  api              = "cf"
  validation_delay = 0

  data = {
    CF_Account_ID = "938405242b51a1caf73f0b661bfb3dc2"
    CF_Zone_ID    = "cec5bf01afed114303a536c264a1f394"
  }

  lifecycle {
    # `data` manually managed
    ignore_changes = [data]
  }
}
