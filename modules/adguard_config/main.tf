locals {
  adguard_dns = {
    blocked_hosts              = ["version.bind", "id.server", "hostname.bind"]
    blocked_response_ttl       = 10
    blocking_mode              = "default"
    bootstrap_dns              = ["9.9.9.10", "149.112.112.10", "2620:fe::10", "2620:fe::fe:10"]
    cache_optimistic           = true
    cache_size                 = 16777216
    cache_ttl_max              = 0
    cache_ttl_min              = 60
    dnssec_enabled             = true
    protection_enabled         = true
    rate_limit                 = 50
    rate_limit_subnet_len_ipv4 = 24
    rate_limit_subnet_len_ipv6 = 56
    resolve_clients            = true
    upstream_dns               = ["https://unfiltered.adguard-dns.com/dns-query", "tls://unfiltered.adguard-dns.com", "https://dns10.quad9.net/dns-query"]
    upstream_mode              = "load_balance"
    upstream_timeout           = 5
    use_private_ptr_resolvers  = false
  }

  adguard_filtering = {
    enabled         = true
    update_interval = 12
  }

  adguard_querylog = {
    anonymize_client_ip = false
    enabled             = true
    interval            = 168 # 7 days
  }

  adguard_stats = {
    enabled  = true
    interval = 720 # 30 days
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

}

resource "adguard_config" "this" {
  dns              = local.adguard_dns
  blocked_services = var.blocked_services
  filtering        = local.adguard_filtering
  parental_control = false
  querylog         = local.adguard_querylog
  safebrowsing     = true
  stats            = local.adguard_stats
  tls              = merge(local.adguard_tls_base, { server_name = var.adguard_server_name })
}

resource "adguard_list_filter" "this" {
  for_each = var.filter_lists

  name    = each.key
  url     = each.value.url
  enabled = each.value.enabled

  depends_on = [adguard_config.this]
}

resource "adguard_user_rules" "this" {
  rules = var.user_rules

  depends_on = [adguard_config.this]
}
