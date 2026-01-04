locals {
  adguard_dns = {
    blocked_hosts              = ["version.bind", "id.server", "hostname.bind"]
    blocked_response_ttl       = 10
    blocking_mode              = "default"
    bootstrap_dns              = ["9.9.9.10", "149.112.112.10", "2620:fe::10", "2620:fe::fe:10"]
    cache_optimistic           = false
    cache_size                 = 4194304
    cache_ttl_max              = 0
    cache_ttl_min              = 0
    dnssec_enabled             = false
    protection_enabled         = true
    rate_limit                 = 20
    rate_limit_subnet_len_ipv4 = 24
    rate_limit_subnet_len_ipv6 = 56
    upstream_dns               = ["https://dns10.quad9.net/dns-query"]
    upstream_mode              = "load_balance"
    upstream_timeout           = 10
    use_private_ptr_resolvers  = false
  }

  adguard_filtering = {
    enabled         = true
    update_interval = 24
  }

  adguard_querylog = {
    anonymize_client_ip = false
    enabled             = true
    interval            = 168
  }

  adguard_stats = {
    enabled  = true
    interval = 720
  }

  adguard_tls_base = {
    enabled            = true
    force_https        = true
    port_dns_over_quic = 853
    port_dns_over_tls  = 853
    port_https         = 443
    serve_plain_dns    = true
    certificate_chain  = base64encode(var.certificate_pem)
    private_key        = base64encode(var.private_key_pem)
  }

  adguard_filters = {
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

resource "adguard_config" "primary" {
  provider = adguard.primary

  dns              = local.adguard_dns
  filtering        = local.adguard_filtering
  parental_control = false
  querylog         = local.adguard_querylog
  safebrowsing     = false
  stats            = local.adguard_stats
  tls              = merge(local.adguard_tls_base, { server_name = var.adguard_primary_server_name })
}

resource "adguard_config" "secondary" {
  provider = adguard.secondary

  dns              = local.adguard_dns
  filtering        = local.adguard_filtering
  parental_control = false
  querylog         = local.adguard_querylog
  safebrowsing     = false
  stats            = local.adguard_stats
  tls              = merge(local.adguard_tls_base, { server_name = var.adguard_secondary_server_name })
}

resource "adguard_list_filter" "primary" {
  provider = adguard.primary
  for_each = local.adguard_filters

  name    = each.key
  url     = each.value.url
  enabled = each.value.enabled

  depends_on = [adguard_config.primary]
}

resource "adguard_list_filter" "secondary" {
  provider = adguard.secondary
  for_each = local.adguard_filters

  name    = each.key
  url     = each.value.url
  enabled = each.value.enabled

  depends_on = [adguard_config.secondary]
}

resource "adguard_user_rules" "primary" {
  provider = adguard.primary
  rules    = local.adguard_user_rules

  depends_on = [adguard_config.primary]
}

resource "adguard_user_rules" "secondary" {
  provider = adguard.secondary
  rules    = local.adguard_user_rules

  depends_on = [adguard_config.secondary]
}
