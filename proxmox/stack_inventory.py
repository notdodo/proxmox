"""Typed inventory for first-class Proxmox resources and workloads."""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import IPv4Address
from typing import TYPE_CHECKING

from proxmox_components import (
    AdGuardAllowRule,
    AdGuardConfig,
    AdGuardDnsConfig,
    AdGuardFilteringConfig,
    AdGuardHttpConfig,
    AdGuardHttpDohConfig,
    AdGuardInstanceConfig,
    AdGuardLogConfig,
    AdGuardTlsConfig,
    BridgeConfig,
    Datastore,
    DebianLxcTemplateConfig,
    FilterListConfig,
    GuestOS,
    PortainerVmConfig,
    ProxmoxNodeConfig,
    UserConfig,
)
from proxmox_components.containers import LxcRuntimeConfig

if TYPE_CHECKING:
    import pulumi

ALL_INTERFACES = IPv4Address(0).compressed


@dataclass(frozen=True)
class AcmeSettings:
    """ACME issuance settings."""

    email_address: pulumi.Input[str]
    cloudflare_api_token: pulumi.Input[str]


@dataclass(frozen=True)
class PoolSpec:
    """First-class Proxmox pool inventory item."""

    resource_name: str
    pool_id: str
    comment: str = "Managed by Pulumi; Resource pool"


@dataclass(frozen=True)
class DownloadedImageSpec:
    """First-class downloadable datastore image."""

    resource_name: str
    content_type: str
    datastore_id: Datastore
    file_name: str
    url: str
    overwrite_unmanaged: bool = True


@dataclass(frozen=True)
class LxcTemplateSpec:
    """First-class reusable LXC template inventory item."""

    resource_name: str
    settings: DebianLxcTemplateConfig
    image_name: str


@dataclass(frozen=True)
class VmIsoRef:
    """Attachment of a first-class downloaded image to a VM."""

    image_name: str
    interface: str


@dataclass(frozen=True)
class VmSpec:
    """First-class generic Proxmox VM inventory item."""

    resource_name: str
    vm_name: str
    os: GuestOS
    iso_attachments: list[VmIsoRef]
    cpu_cores: int
    memory_mb: int
    disk_size_gb: int
    description: str
    tags: list[str]
    pool_name: str | None = None


@dataclass(frozen=True)
class PortainerSpec:
    """Portainer workload inventory item referencing first-class resources."""

    image_name: str
    pool_name: str
    settings: PortainerVmConfig


@dataclass(frozen=True)
class AdGuardSpec:
    """AdGuard workload inventory item referencing first-class resources."""

    template_name: str
    settings: AdGuardConfig


@dataclass(frozen=True)
class ProductionInventory:
    """Production stack inventory."""

    node: ProxmoxNodeConfig
    bridges: list[BridgeConfig]
    foundation_users: list[UserConfig]
    acme: AcmeSettings
    pools: list[PoolSpec]
    images: list[DownloadedImageSpec]
    lxc_templates: list[LxcTemplateSpec]
    vms: list[VmSpec]
    portainer: PortainerSpec
    adguard: AdGuardSpec


def production_inventory(config: pulumi.Config) -> ProductionInventory:
    """Build the production inventory from Pulumi config and defaults."""
    return ProductionInventory(
        node=ProxmoxNodeConfig(
            name=config.require("proxmox_node_name"),
            management_cidr=config.require("proxmox_node_cidr"),
            default_bridge_name="vmbr0",
            default_gateway="192.168.178.1",
            uplink_ports=["nic0"],
        ),
        bridges=[
            BridgeConfig(
                resource_name="default",
                name="vmbr0",
                address=config.require("proxmox_node_cidr"),
                gateway="192.168.178.1",
                uplink_ports=["nic0"],
                comment="Managed by Pulumi; Primary LAN bridge",
            ),
            BridgeConfig(
                resource_name="services",
                name="vmbr100",
                address="10.0.100.0/24",
                uplink_ports=None,
                comment="Managed by Pulumi; Services network bridge",
                import_id=f"{config.require('proxmox_node_name')}:vmbr100",
            ),
        ],
        foundation_users=[
            UserConfig(
                username="operations-automation",
                role_id="Operations",
                pam_enabled=False,
            )
        ],
        acme=AcmeSettings(
            email_address=config.require_secret("acme_email_address"),
            cloudflare_api_token=config.require_secret("cf_api_token"),
        ),
        pools=[
            PoolSpec(
                resource_name="workload-pool",
                pool_id="portainer",
                comment="Managed by Pulumi; Shared workload pool",
            ),
        ],
        images=[
            DownloadedImageSpec(
                resource_name="ubuntu-cloud-image",
                content_type="import",
                datastore_id=Datastore.LOCAL,
                file_name="ubuntu-24.04-server-cloudimg-amd64.qcow2",
                url="https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-amd64.img",
            ),
            DownloadedImageSpec(
                resource_name="windows-iso",
                content_type="iso",
                datastore_id=Datastore.LOCAL,
                file_name="win11-enterprise.iso",
                url="https://software-static.download.prss.microsoft.com/dbazure/888969d5-f34g-4e03-ac9d-1f9786c66749/26100.1742.240906-0331.ge_release_svc_refresh_CLIENTENTERPRISEEVAL_OEMRET_x64FRE_en-us.iso",
            ),
            DownloadedImageSpec(
                resource_name="virtio-iso",
                content_type="iso",
                datastore_id=Datastore.LOCAL,
                file_name="virtio-win.iso",
                url="https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso",
            ),
            DownloadedImageSpec(
                resource_name="debian-13-lxc-image",
                content_type="vztmpl",
                datastore_id=Datastore.LOCAL,
                file_name="debian-13-standard_13.1-2_amd64.tar.zst",
                url="http://download.proxmox.com/images/system/debian-13-standard_13.1-2_amd64.tar.zst",
            ),
        ],
        lxc_templates=[
            LxcTemplateSpec(
                resource_name="debian-template",
                image_name="debian-13-lxc-image",
                settings=DebianLxcTemplateConfig(
                    vm_id=8000,
                    hostname="debian-template",
                    description="Managed by Pulumi; Debian 13 standard LXC template (SSH enabled)",
                    rootfs_datastore_id=Datastore.LOCAL_LVM,
                    rootfs_size_gb=2,
                    start_on_boot=False,
                    started=False,
                    unprivileged=True,
                    nesting=True,
                    tags=["debian", "lxc"],
                ),
            )
        ],
        vms=[
            VmSpec(
                resource_name="win11",
                vm_name="Win11",
                os=GuestOS.WIN11,
                iso_attachments=[
                    VmIsoRef(image_name="windows-iso", interface="ide2"),
                    VmIsoRef(image_name="virtio-iso", interface="ide3"),
                ],
                cpu_cores=4,
                memory_mb=1024 * 6,
                disk_size_gb=64,
                description="Managed by Pulumi; Generic Win11 evaluation VM",
                tags=["win11"],
                pool_name="workload-pool",
            )
        ],
        portainer=PortainerSpec(
            image_name="ubuntu-cloud-image",
            pool_name="workload-pool",
            settings=PortainerVmConfig(
                vm_id=110,
                vm_name="Portainer",
                hostname="portainer",
                fqdn="portainer.thedodo.xyz",
                ip_address="192.168.178.210/24",
                gateway="192.168.178.1",
                dns_servers=["1.1.1.1", "8.8.8.8"],
                disk_datastore_id=Datastore.LOCAL_LVM,
                admin_username="notdodo",
                pool_id=None,
            ),
        ),
        adguard=AdGuardSpec(
            template_name="debian-template",
            settings=AdGuardConfig(
                version="v0.107.74",
                admin_username="notdodo",
                http=AdGuardHttpConfig(
                    bind_host=ALL_INTERFACES,
                    port=80,
                    session_ttl="720h",
                    auth_attempts=5,
                    block_auth_min=15,
                ),
                http_doh=AdGuardHttpDohConfig(
                    insecure_enabled=False,
                    routes=[
                        "GET /dns-query",
                        "POST /dns-query",
                        "GET /dns-query/{ClientID}",
                        "POST /dns-query/{ClientID}",
                    ],
                ),
                dns=AdGuardDnsConfig(
                    bind_hosts=[ALL_INTERFACES],
                    port=53,
                    cache_enabled=True,
                    blocked_hosts=["version.bind", "id.server", "hostname.bind"],
                    blocked_response_ttl=10,
                    blocking_mode="default",
                    bootstrap_dns=[
                        "9.9.9.10",
                        "149.112.112.10",
                        "2620:fe::10",
                        "2620:fe::fe:10",
                    ],
                    cache_optimistic=True,
                    cache_optimistic_answer_ttl="30s",
                    cache_optimistic_max_age="12h",
                    cache_size=16777216,
                    cache_ttl_max=0,
                    cache_ttl_min=60,
                    dnssec_enabled=True,
                    protection_enabled=True,
                    rate_limit=50,
                    rate_limit_subnet_len_ipv4=24,
                    rate_limit_subnet_len_ipv6=56,
                    resolve_clients=True,
                    upstream_dns=[
                        "https://unfiltered.adguard-dns.com/dns-query",
                        "tls://unfiltered.adguard-dns.com",
                        "https://dns10.quad9.net/dns-query",
                    ],
                    upstream_mode="load_balance",
                    upstream_timeout="5s",
                    use_private_ptr_resolvers=False,
                ),
                filtering=AdGuardFilteringConfig(
                    protection_enabled=True,
                    filtering_enabled=True,
                    blocking_mode="default",
                    filters_update_interval=12,
                    parental_enabled=False,
                    safebrowsing_enabled=True,
                ),
                query_log=AdGuardLogConfig(
                    enabled=True,
                    interval="168h",
                    ignored=[],
                    ignored_enabled=False,
                ),
                statistics=AdGuardLogConfig(
                    enabled=True,
                    interval="720h",
                    ignored=[],
                    ignored_enabled=False,
                ),
                tls=AdGuardTlsConfig(
                    enabled=True,
                    force_https=True,
                    port_https=443,
                    port_dns_over_tls=853,
                    port_dns_over_quic=853,
                    serve_plain_dns=True,
                ),
                blocked_services=[
                    "betano",
                    "betfair",
                    "betway",
                    "blaze",
                    "deepseek",
                    "temu",
                    "xiaohongshu",
                ],
                filter_lists=[
                    FilterListConfig(
                        name="AdGuard DNS filter",
                        enabled=True,
                        url="https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt",
                    ),
                    FilterListConfig(
                        name="AdAway Default Blocklist",
                        enabled=True,
                        url="https://adguardteam.github.io/HostlistsRegistry/assets/filter_2.txt",
                    ),
                    FilterListConfig(
                        name="Dan Pollock's List",
                        enabled=True,
                        url="https://adguardteam.github.io/HostlistsRegistry/assets/filter_4.txt",
                    ),
                    FilterListConfig(
                        name="HaGeZi's Ultimate Blocklist",
                        enabled=True,
                        url="https://adguardteam.github.io/HostlistsRegistry/assets/filter_49.txt",
                    ),
                    FilterListConfig(
                        name="AdGuard DNS Popup Hosts filter",
                        enabled=True,
                        url="https://adguardteam.github.io/HostlistsRegistry/assets/filter_59.txt",
                    ),
                    FilterListConfig(
                        name="uBlock0 filters - Badware risks",
                        enabled=True,
                        url="https://adguardteam.github.io/HostlistsRegistry/assets/filter_50.txt",
                    ),
                    FilterListConfig(
                        name="Malicious URL Blocklist (URLHaus)",
                        enabled=True,
                        url="https://adguardteam.github.io/HostlistsRegistry/assets/filter_11.txt",
                    ),
                ],
                allow_rules=[
                    AdGuardAllowRule(domain="graph.facebook.com", important=True),
                    AdGuardAllowRule(domain="mask-h2.icloud.com", important=True),
                    AdGuardAllowRule(domain="mask.icloud.com", important=True),
                    AdGuardAllowRule(domain="metrics.icloud.com", important=True),
                    AdGuardAllowRule(
                        domain="o4505093097586688.ingest.us.sentry.io", important=True
                    ),
                    AdGuardAllowRule(domain="teamsystem.musvc2.net", important=True),
                    AdGuardAllowRule(domain="web.facebook.com", important=True),
                ],
                user_rules=[],
                lxc_runtime=LxcRuntimeConfig(
                    rootfs_datastore_id=Datastore.LOCAL_LVM,
                    rootfs_size_gb=2,
                    start_on_boot=True,
                    started=True,
                    unprivileged=True,
                    nesting=True,
                    tags=["adguard", "lxc"],
                    timeout_clone=1800,
                    timeout_create=1800,
                    timeout_delete=60,
                    timeout_update=1800,
                ),
                instances=[
                    AdGuardInstanceConfig(
                        hostname="adguard",
                        server_name="adguard.thedodo.xyz",
                        vm_id=500,
                        ip_address="192.168.178.200/24",
                        gateway="192.168.178.1",
                    ),
                    AdGuardInstanceConfig(
                        hostname="adguard2",
                        server_name="adguard2.thedodo.xyz",
                        vm_id=501,
                        ip_address="192.168.178.201/24",
                        gateway="192.168.178.1",
                    ),
                ],
            ),
        ),
    )
