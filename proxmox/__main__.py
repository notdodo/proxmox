"""Pulumi entrypoint for the Proxmox homelab project."""

from dataclasses import replace

import pulumi
import pulumi_proxmoxve as proxmoxve
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
from stack_inventory import production_inventory


def main() -> None:
    """Define the production homelab stack."""
    config = pulumi.Config("proxmox-homelab")
    inventory = production_inventory(config)
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

    foundation = HomelabFoundation(
        "foundation",
        node=inventory.node,
        bridges=inventory.bridges,
        users=inventory.foundation_users,
        opts=proxmox_opts,
    )

    image_resources = {
        image.resource_name: File(
            image.resource_name,
            content_type=image.content_type,
            datastore_id=image.datastore_id,
            file_name=image.file_name,
            node_name=inventory.node.name,
            overwrite_unmanaged=image.overwrite_unmanaged,
            url=image.url,
            opts=proxmox_opts,
        )
        for image in inventory.images
    }

    pool_resources = {
        pool.resource_name: PoolLegacy(
            pool.resource_name,
            pool_id=pool.pool_id,
            comment=pool.comment,
            opts=proxmox_opts,
        )
        for pool in inventory.pools
    }

    template_resources = {
        template.resource_name: DebianLxcTemplate(
            template.resource_name,
            node_name=inventory.node.name,
            image_file_id=image_resources[template.image_name].id,
            settings=template.settings,
            opts=proxmox_opts,
        )
        for template in inventory.lxc_templates
    }

    acme_provider = acme.Provider(
        "acme",
        server_url="https://acme-v02.api.letsencrypt.org/directory",
    )
    registration = acme.Registration(
        "registration",
        email_address=inventory.acme.email_address,
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
                config={"CF_DNS_API_TOKEN": inventory.acme.cloudflare_api_token},
            ),
        ],
        opts=pulumi.ResourceOptions(provider=acme_provider),
    )

    portainer_pool = pool_resources[inventory.portainer.pool_name]
    PortainerVm(
        "portainer",
        node_name=inventory.node.name,
        network_bridge=foundation.default_network_name,
        image_file_id=image_resources[inventory.portainer.image_name].id,
        certificate_pem=certificate.certificate_pem,
        issuer_pem=certificate.issuer_pem,
        private_key_pem=certificate.private_key_pem,
        settings=replace(inventory.portainer.settings, pool_id=portainer_pool.pool_id),
        opts=proxmox_opts,
    )

    adguard_template = template_resources[inventory.adguard.template_name]
    AdGuardContainers(
        "adguard",
        node_name=inventory.node.name,
        settings=inventory.adguard.settings,
        template_vm_id=adguard_template.vm_id,
        ssh_private_key=adguard_template.ssh_private_key,
        default_network_name=foundation.default_network_name,
        certificate_pem=certificate.certificate_pem,
        private_key_pem=certificate.private_key_pem,
        opts=proxmox_opts,
    )

    for vm in inventory.vms:
        pool_id = pool_resources[vm.pool_name].pool_id if vm.pool_name else None
        ProxmoxVm(
            vm.resource_name,
            node_name=inventory.node.name,
            network_bridge=foundation.default_network_name,
            vm_name=vm.vm_name,
            os=GuestOS(vm.os),
            isos=[
                IsoAttachment(
                    file_id=image_resources[attachment.image_name].id,
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
            opts=proxmox_opts,
        )


main()
