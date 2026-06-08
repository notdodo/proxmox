"""Production stack composition for the Proxmox homelab project."""

from __future__ import annotations

from dataclasses import dataclass, replace

import pulumi
import pulumiverse_acme as acme
from pulumi_proxmoxve.download.file import File
from pulumi_proxmoxve.pool_legacy import PoolLegacy

from proxmox_components import (
    AdGuardContainers,
    DebianLxcTemplate,
    GuestOS,
    HomelabFoundation,
    IsoAttachment,
    PortainerVm,
    ProxmoxVm,
)

from .provider import ProxmoxProviderOptions, create_proxmox_provider_options
from .settings import ProductionSettings, build_production_settings
from .stacks import HomelabEnvironment, current_stack


@dataclass
class DownloadedResources:
    """Downloaded first-class resources keyed by settings resource name."""

    images: dict[str, File]
    lxc_templates: dict[str, DebianLxcTemplate]
    pools: dict[str, PoolLegacy]


def deploy_current_stack() -> None:
    """Deploy the active Pulumi stack."""
    stack = current_stack()
    if stack.env == HomelabEnvironment.PRODUCTION:
        deploy_production()
        return

    msg = f"Unsupported stack environment: {stack.env}"
    raise ValueError(msg)


def deploy_production() -> None:
    """Deploy the production homelab stack."""
    config = pulumi.Config("proxmox-homelab")
    settings = build_production_settings(config)
    proxmox_opts = create_proxmox_provider_options(config)

    foundation = _create_foundation(settings, proxmox_opts.component)
    downloaded = _create_downloaded_resources(settings, proxmox_opts)
    certificate = _create_wildcard_certificate(settings)

    _deploy_portainer(
        settings,
        foundation,
        downloaded,
        certificate,
        proxmox_opts.component,
    )
    _deploy_adguard(
        settings, foundation, downloaded, certificate, proxmox_opts.component
    )
    _deploy_generic_vms(settings, foundation, downloaded, proxmox_opts)


def _create_foundation(
    settings: ProductionSettings,
    opts: pulumi.ResourceOptions,
) -> HomelabFoundation:
    return HomelabFoundation(
        "foundation",
        node=settings.node,
        bridges=settings.bridges,
        users=settings.foundation_users,
        opts=opts,
    )


def _create_downloaded_resources(
    settings: ProductionSettings,
    opts: ProxmoxProviderOptions,
) -> DownloadedResources:
    images = {
        image.resource_name: File(
            image.resource_name,
            checksum=image.checksum,
            checksum_algorithm=image.checksum_algorithm,
            content_type=image.content_type,
            datastore_id=image.datastore_id,
            file_name=image.file_name,
            node_name=settings.node.name,
            overwrite=image.overwrite,
            overwrite_unmanaged=image.overwrite_unmanaged,
            upload_timeout=image.upload_timeout,
            url=image.url,
            verify=image.verify,
            opts=opts.resource,
        )
        for image in settings.images
    }

    pools = {
        pool.resource_name: PoolLegacy(
            pool.resource_name,
            pool_id=pool.pool_id,
            comment=pool.comment,
            opts=opts.resource,
        )
        for pool in settings.pools
    }

    lxc_templates = {
        template.resource_name: DebianLxcTemplate(
            template.resource_name,
            node_name=settings.node.name,
            image_file_id=images[template.image_name].id,
            settings=template.settings,
            opts=opts.component,
        )
        for template in settings.lxc_templates
    }

    return DownloadedResources(
        images=images,
        lxc_templates=lxc_templates,
        pools=pools,
    )


def _create_wildcard_certificate(settings: ProductionSettings) -> acme.Certificate:
    acme_provider = acme.Provider(
        "acme",
        server_url="https://acme-v02.api.letsencrypt.org/directory",
    )
    registration = acme.Registration(
        "registration",
        email_address=settings.acme.email_address,
        opts=pulumi.ResourceOptions(provider=acme_provider),
    )
    return acme.Certificate(
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
                config={"CF_DNS_API_TOKEN": settings.acme.cloudflare_api_token},
            ),
        ],
        opts=pulumi.ResourceOptions(provider=acme_provider),
    )


def _deploy_portainer(
    settings: ProductionSettings,
    foundation: HomelabFoundation,
    resources: DownloadedResources,
    certificate: acme.Certificate,
    opts: pulumi.ResourceOptions,
) -> None:
    portainer_pool = resources.pools[settings.portainer.pool_name]
    PortainerVm(
        "portainer",
        node_name=settings.node.name,
        network_bridge=foundation.default_network_name,
        image_file_id=resources.images[settings.portainer.image_name].id,
        certificate_pem=certificate.certificate_pem,
        issuer_pem=certificate.issuer_pem,
        private_key_pem=certificate.private_key_pem,
        settings=replace(
            settings.portainer.settings,
            pool_id=portainer_pool.pool_id,
        ),
        opts=opts,
    )


def _deploy_adguard(
    settings: ProductionSettings,
    foundation: HomelabFoundation,
    resources: DownloadedResources,
    certificate: acme.Certificate,
    opts: pulumi.ResourceOptions,
) -> None:
    adguard_template = resources.lxc_templates[settings.adguard.template_name]
    AdGuardContainers(
        "adguard",
        node_name=settings.node.name,
        settings=settings.adguard.settings,
        template_vm_id=adguard_template.vm_id,
        ssh_private_key=adguard_template.ssh_private_key,
        default_network_name=foundation.default_network_name,
        certificate_pem=certificate.certificate_pem,
        private_key_pem=certificate.private_key_pem,
        opts=opts,
    )


def _deploy_generic_vms(
    settings: ProductionSettings,
    foundation: HomelabFoundation,
    resources: DownloadedResources,
    opts: ProxmoxProviderOptions,
) -> None:
    for vm in settings.vms:
        pool_id = resources.pools[vm.pool_name].pool_id if vm.pool_name else None
        ProxmoxVm(
            vm.resource_name,
            node_name=settings.node.name,
            network_bridge=foundation.default_network_name,
            vm_name=vm.vm_name,
            os=GuestOS(vm.os),
            isos=[
                IsoAttachment(
                    file_id=resources.images[attachment.image_name].id,
                    interface=attachment.interface,
                )
                for attachment in vm.iso_attachments
            ],
            cpu_cores=vm.cpu_cores,
            memory_mb=vm.memory_mb,
            disk_size_gb=vm.disk_size_gb,
            description=vm.description,
            tags=vm.tags,
            pool_id=pool_id,
            performance=vm.performance,
            proxmox_host_connection=opts.host_connection,
            opts=opts.component,
        )
