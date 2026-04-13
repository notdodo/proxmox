"""AdGuard Home configuration rendering helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from textwrap import indent

import pulumi


@dataclass(frozen=True)
class FilterListConfig:
    """Filter list configuration entry."""

    name: str
    enabled: bool
    url: str


@dataclass(frozen=True)
class AdGuardHttpConfig:
    """AdGuard HTTP admin surface settings."""

    bind_host: str
    port: int
    session_ttl: str
    auth_attempts: int
    block_auth_min: int


@dataclass(frozen=True)
class AdGuardDnsConfig:
    """AdGuard DNS runtime settings."""

    bind_hosts: list[str]
    port: int
    blocked_hosts: list[str]
    blocked_response_ttl: int
    blocking_mode: str
    bootstrap_dns: list[str]
    cache_optimistic: bool
    cache_size: int
    cache_ttl_max: int
    cache_ttl_min: int
    dnssec_enabled: bool
    protection_enabled: bool
    rate_limit: int
    rate_limit_subnet_len_ipv4: int
    rate_limit_subnet_len_ipv6: int
    resolve_clients: bool
    upstream_dns: list[str]
    upstream_mode: str
    upstream_timeout: str
    use_private_ptr_resolvers: bool


@dataclass(frozen=True)
class AdGuardFilteringConfig:
    """AdGuard filtering settings."""

    protection_enabled: bool
    filtering_enabled: bool
    blocking_mode: str
    filters_update_interval: int
    parental_enabled: bool
    safebrowsing_enabled: bool


@dataclass(frozen=True)
class AdGuardLogConfig:
    """AdGuard query log and statistics retention settings."""

    enabled: bool
    interval: str


@dataclass(frozen=True)
class AdGuardTlsConfig:
    """AdGuard TLS listener settings independent of certificate material."""

    enabled: bool
    force_https: bool
    port_https: int
    port_dns_over_tls: int
    port_dns_over_quic: int
    serve_plain_dns: bool


def render_yaml_list(items: list[str], *, indent_level: int) -> list[str]:
    """Render a simple YAML list with JSON-escaped values."""
    prefix = " " * indent_level
    return [f"{prefix}- {json.dumps(item)}" for item in items]


def render_yaml_filter_entries(
    filters: list[FilterListConfig],
    *,
    indent_level: int,
) -> list[str]:
    """Render AdGuard filter-list entries."""
    prefix = " " * indent_level
    lines: list[str] = []
    for index, filter_config in enumerate(filters, start=1):
        lines.extend(
            [
                f"{prefix}- enabled: {str(filter_config.enabled).lower()}",
                f"{prefix}  url: {json.dumps(filter_config.url)}",
                f"{prefix}  name: {json.dumps(filter_config.name)}",
                f"{prefix}  id: {index}",
            ],
        )
    return lines


def render_adguard_config(
    *,
    username: str,
    password_bcrypt: pulumi.Input[str],
    server_name: str,
    http: AdGuardHttpConfig,
    dns: AdGuardDnsConfig,
    filtering: AdGuardFilteringConfig,
    query_log: AdGuardLogConfig,
    statistics: AdGuardLogConfig,
    tls: AdGuardTlsConfig,
    blocked_services: list[str],
    filter_lists: list[FilterListConfig],
    user_rules: list[str],
    cert_pem: pulumi.Input[str],
    private_key_pem: pulumi.Input[str],
) -> pulumi.Output[str]:
    """Render the AdGuardHome YAML configuration."""
    return pulumi.Output.all(password_bcrypt, cert_pem, private_key_pem).apply(
        lambda args: "\n".join(
            [
                "http:",
                f"  address: {http.bind_host}:{http.port}",
                f"  session_ttl: {http.session_ttl}",
                "users:",
                f"  - name: {json.dumps(username)}",
                f"    password: {json.dumps(args[0])}",
                f"auth_attempts: {http.auth_attempts}",
                f"block_auth_min: {http.block_auth_min}",
                "dns:",
                "  bind_hosts:",
                *render_yaml_list(dns.bind_hosts, indent_level=4),
                f"  port: {dns.port}",
                "  blocked_hosts:",
                *render_yaml_list(dns.blocked_hosts, indent_level=4),
                f"  blocked_response_ttl: {dns.blocked_response_ttl}",
                f"  blocking_mode: {dns.blocking_mode}",
                "  bootstrap_dns:",
                *render_yaml_list(dns.bootstrap_dns, indent_level=4),
                f"  cache_optimistic: {str(dns.cache_optimistic).lower()}",
                f"  cache_size: {dns.cache_size}",
                f"  cache_ttl_max: {dns.cache_ttl_max}",
                f"  cache_ttl_min: {dns.cache_ttl_min}",
                f"  dnssec_enabled: {str(dns.dnssec_enabled).lower()}",
                f"  protection_enabled: {str(dns.protection_enabled).lower()}",
                f"  rate_limit: {dns.rate_limit}",
                f"  rate_limit_subnet_len_ipv4: {dns.rate_limit_subnet_len_ipv4}",
                f"  rate_limit_subnet_len_ipv6: {dns.rate_limit_subnet_len_ipv6}",
                f"  resolve_clients: {str(dns.resolve_clients).lower()}",
                "  upstream_dns:",
                *render_yaml_list(dns.upstream_dns, indent_level=4),
                f"  upstream_mode: {dns.upstream_mode}",
                f"  upstream_timeout: {dns.upstream_timeout}",
                f"  use_private_ptr_resolvers: {str(dns.use_private_ptr_resolvers).lower()}",
                "filtering:",
                f"  protection_enabled: {str(filtering.protection_enabled).lower()}",
                f"  filtering_enabled: {str(filtering.filtering_enabled).lower()}",
                f"  blocking_mode: {filtering.blocking_mode}",
                f"  filters_update_interval: {filtering.filters_update_interval}",
                f"  parental_enabled: {str(filtering.parental_enabled).lower()}",
                f"  safebrowsing_enabled: {str(filtering.safebrowsing_enabled).lower()}",
                "  blocked_services:",
                "    ids:",
                *render_yaml_list(blocked_services, indent_level=6),
                "querylog:",
                f"  enabled: {str(query_log.enabled).lower()}",
                f"  interval: {query_log.interval}",
                "statistics:",
                f"  enabled: {str(statistics.enabled).lower()}",
                f"  interval: {statistics.interval}",
                "tls:",
                f"  enabled: {str(tls.enabled).lower()}",
                f"  server_name: {json.dumps(server_name)}",
                f"  force_https: {str(tls.force_https).lower()}",
                f"  port_https: {tls.port_https}",
                f"  port_dns_over_tls: {tls.port_dns_over_tls}",
                f"  port_dns_over_quic: {tls.port_dns_over_quic}",
                f"  serve_plain_dns: {str(tls.serve_plain_dns).lower()}",
                "  certificate_chain: |-",
                indent(args[1].strip(), " " * 4),
                "  private_key: |-",
                indent(args[2].strip(), " " * 4),
                "filters:",
                *render_yaml_filter_entries(filter_lists, indent_level=2),
                "user_rules:",
                *render_yaml_list(user_rules, indent_level=2),
                "schema_version: 29",
            ],
        ),
    )
