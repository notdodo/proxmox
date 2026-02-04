locals {
  remote_state_bucket = "notdodo-terraform"
  remote_state_key    = "proxmox"
  remote_state_region = "eu-west-1"

  adguard_admin_username = "notdodo"
  adguard_scheme         = "https"
  adguard_tls_insecure   = true

  adguard_instances = {
    primary = {
      host        = "192.168.178.200:443"
      server_name = "adguard.thedodo.xyz"
    }
    secondary = {
      host        = "192.168.178.201:443"
      server_name = "adguard2.thedodo.xyz"
    }
  }

  adguard_blocked_services = ["betano", "betfair", "betway", "blaze", "deepseek", "temu", "xiaohongshu"]

  adguard_filter_lists = {
    "AdGuard DNS filter" = {
      enabled = true
      url     = "https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt"
    }
    "AdAway Default Blocklist" = {
      enabled = true
      url     = "https://adguardteam.github.io/HostlistsRegistry/assets/filter_2.txt"
    }
    "Dan Pollock's List" = {
      enabled = true
      url     = "https://adguardteam.github.io/HostlistsRegistry/assets/filter_4.txt"
    }
    "HaGeZi's Ultimate Blocklist" = {
      enabled = true
      url     = "https://adguardteam.github.io/HostlistsRegistry/assets/filter_49.txt"
    }
    "AdGuard DNS Popup Hosts filter" = {
      enabled = true
      url     = "https://adguardteam.github.io/HostlistsRegistry/assets/filter_59.txt"
    }
    "uBlock0 filters - Badware risks" = {
      enabled = true
      url     = "https://adguardteam.github.io/HostlistsRegistry/assets/filter_50.txt"
    }
    "Malicious URL Blocklist (URLHaus)" = {
      enabled = true
      url     = "https://adguardteam.github.io/HostlistsRegistry/assets/filter_11.txt"
    }
  }

  adguard_user_rules = [
    "@@||o4505093097586688.ingest.us.sentry.io^$important",
    "# Disable iCloud Private Relay",
    "@@||mask.icloud.com^$important",
    "@@||mask-h2.icloud.com^$important",
    "@@||metrics.icloud.com^$important",
  ]
}

data "terraform_remote_state" "homelab" {
  backend = "s3"
  config = {
    bucket = local.remote_state_bucket
    key    = local.remote_state_key
    region = local.remote_state_region
  }
}

module "adguard_config_primary" {
  source = "../modules/adguard_config"

  adguard_server_name = local.adguard_instances.primary.server_name
  blocked_services    = local.adguard_blocked_services
  filter_lists        = local.adguard_filter_lists
  user_rules          = local.adguard_user_rules

  certificate_pem = data.terraform_remote_state.homelab.outputs.acme_certificate_pem
  private_key_pem = data.terraform_remote_state.homelab.outputs.acme_private_key_pem

  providers = {
    adguard = adguard.primary
  }
}

module "adguard_config_secondary" {
  source = "../modules/adguard_config"

  adguard_server_name = local.adguard_instances.secondary.server_name
  blocked_services    = local.adguard_blocked_services
  filter_lists        = local.adguard_filter_lists
  user_rules          = local.adguard_user_rules

  certificate_pem = data.terraform_remote_state.homelab.outputs.acme_certificate_pem
  private_key_pem = data.terraform_remote_state.homelab.outputs.acme_private_key_pem

  providers = {
    adguard = adguard.secondary
  }
}

provider "adguard" {
  alias    = "primary"
  host     = local.adguard_instances.primary.host
  scheme   = local.adguard_scheme
  username = local.adguard_admin_username
  password = var.adguard_password
  insecure = local.adguard_tls_insecure
  timeout  = 20
}

provider "adguard" {
  alias    = "secondary"
  host     = local.adguard_instances.secondary.host
  scheme   = local.adguard_scheme
  username = local.adguard_admin_username
  password = var.adguard_password
  insecure = local.adguard_tls_insecure
  timeout  = 20
}
