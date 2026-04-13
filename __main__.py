"""Pulumi entrypoint for the Proxmox homelab project."""

import pulumi
import pulumi_proxmoxve as proxmoxve
import pulumiverse_acme as acme
from pulumi_proxmoxve.download.file import File as DownloadFile
from pulumi_proxmoxve.pool_legacy import PoolLegacy as Pool

from proxmox_components import (
    AdGuardContainers,
    AdGuardDnsConfig,
    AdGuardFilteringConfig,
    AdGuardHttpConfig,
    AdGuardInstanceConfig,
    AdGuardLogConfig,
    AdGuardTlsConfig,
    Datastore,
    DebianLxcTemplateConfig,
    FilterListConfig,
    GuestOS,
    HomelabFoundation,
    IsoAttachment,
    LxcRuntimeConfig,
    ProxmoxNodeConfig,
    ProxmoxVm,
    UserConfig,
)

ALL_INTERFACES = "0.0.0.0"  # noqa: S104


def main() -> None:
    """Define the production homelab stack."""
    config = pulumi.Config("proxmox-homelab")
    proxmox_insecure = config.get_bool("proxmox_insecure")

    proxmox_provider = proxmoxve.Provider(
        "proxmox-provider",
        endpoint=config.get("proxmox_endpoint") or "https://proxmox.thedodo.xyz:8006/",
        insecure=proxmox_insecure if proxmox_insecure is not None else True,
        username=config.get("proxmox_automation_user") or "root@pam",
        password=config.require_secret("proxmox_password"),
        ssh=proxmoxve.ProviderSshArgs(agent=True, username="root"),
    )
    proxmox_opts = pulumi.ResourceOptions(providers=[proxmox_provider])

    node = ProxmoxNodeConfig(
        name=config.require("proxmox_node_name"),
        management_cidr=config.require("proxmox_node_cidr"),
        default_bridge_name="vmbr0",
        default_gateway="192.168.178.1",
        uplink_ports=["nic0"],
    )

    foundation = HomelabFoundation(
        "foundation",
        node=node,
        users=[
            UserConfig(
                username="operations-automation",
                role_id="Operations",
                pam_enabled=False,
            ),
        ],
        lxc_template=DebianLxcTemplateConfig(
            vm_id=8000,
            hostname="debian-template",
            description="Managed by Pulumi; Debian 13 standard LXC template (SSH enabled)",
            image_url="http://download.proxmox.com/images/system/debian-13-standard_13.1-2_amd64.tar.zst",
            image_datastore_id=Datastore.LOCAL,
            rootfs_datastore_id=Datastore.LOCAL_LVM,
            rootfs_size_gb=2,
            start_on_boot=False,
            started=False,
            unprivileged=True,
            nesting=True,
            tags=["debian", "lxc"],
        ),
        opts=proxmox_opts,
    )

    acme_provider = acme.Provider(
        "acme",
        server_url="https://acme-v02.api.letsencrypt.org/directory",
    )

    registration = acme.Registration(
        "registration",
        email_address=config.require_secret("acme_email_address"),
        opts=pulumi.ResourceOptions(provider=acme_provider),
    )
    certificate = acme.Certificate(
        "thedodo",
        account_key_pem=registration.account_key_pem,
        common_name="*.thedodo.xyz",
        pre_check_delay=30,
        disable_complete_propagation=True,
        recursive_nameservers=[
            "1.1.1.1:53",
            "1.0.0.1:53",
            "8.8.8.8:53",
        ],
        dns_challenges=[
            acme.CertificateDnsChallengeArgs(
                provider="cloudflare",
                config={"CF_DNS_API_TOKEN": config.require_secret("cf_api_token")},
            ),
        ],
        opts=pulumi.ResourceOptions(provider=acme_provider),
    )

    AdGuardContainers(
        "adguard",
        node_name=node.name,
        version="v0.107.73",
        admin_username="notdodo",
        http=AdGuardHttpConfig(
            bind_host=ALL_INTERFACES,
            port=80,
            session_ttl="720h",
            auth_attempts=5,
            block_auth_min=15,
        ),
        dns=AdGuardDnsConfig(
            bind_hosts=[ALL_INTERFACES],
            port=53,
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
        query_log=AdGuardLogConfig(enabled=True, interval="168h"),
        statistics=AdGuardLogConfig(enabled=True, interval="720h"),
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
        user_rules=[
            "@@||o4505093097586688.ingest.us.sentry.io^$important",
            "# Disable iCloud Private Relay",
            "@@||mask.icloud.com^$important",
            "@@||mask-h2.icloud.com^$important",
            "@@||metrics.icloud.com^$important",
        ],
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
        template_vm_id=foundation.lxc_template_vm_id,
        ssh_private_key=foundation.lxc_template_ssh_private_key,
        default_network_name=foundation.default_network_name,
        certificate_pem=certificate.certificate_pem,
        private_key_pem=certificate.private_key_pem,
        opts=proxmox_opts,
    )

    windows_iso = DownloadFile(
        "windows-iso",
        content_type="iso",
        datastore_id=Datastore.LOCAL,
        file_name="win11-enterprise.iso",
        node_name=node.name,
        overwrite_unmanaged=True,
        url="https://software-static.download.prss.microsoft.com/dbazure/888969d5-f34g-4e03-ac9d-1f9786c66749/26100.1742.240906-0331.ge_release_svc_refresh_CLIENTENTERPRISEEVAL_OEMRET_x64FRE_en-us.iso",
        opts=proxmox_opts,
    )
    virtio_iso = DownloadFile(
        "virtio-iso",
        content_type="iso",
        datastore_id=Datastore.LOCAL,
        file_name="virtio-win.iso",
        node_name=node.name,
        overwrite_unmanaged=True,
        url="https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso",
        opts=proxmox_opts,
    )
    win11_pool = Pool(
        "win11-pool",
        pool_id="portainer",
        comment="Managed by Pulumi",
        opts=proxmox_opts,
    )

    ProxmoxVm(
        "win11",
        node_name=node.name,
        network_bridge=foundation.default_network_name,
        vm_name="Win11",
        os=GuestOS.WIN11,
        isos=[
            IsoAttachment(file_id=windows_iso.id, interface="ide2"),
            IsoAttachment(file_id=virtio_iso.id, interface="ide3"),
        ],
        cpu_cores=4,
        memory_mb=1024 * 6,
        disk_size_gb=64,
        description="Generic Win11 Evaluation",
        tags=["win11"],
        pool_id=win11_pool.pool_id,
        opts=proxmox_opts,
    )


main()
