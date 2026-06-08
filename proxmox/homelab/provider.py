"""Provider configuration for the Proxmox homelab stack."""

from __future__ import annotations

from dataclasses import dataclass

import pulumi
import pulumi_proxmoxve as proxmoxve
from pulumi_command.remote import ConnectionArgs

from proxmox_components.helpers import host_from_cidr


@dataclass
class ProxmoxProviderOptions:
    """Resource options for Proxmox components and first-class resources."""

    component: pulumi.ResourceOptions
    host_connection: ConnectionArgs
    resource: pulumi.ResourceOptions


def create_proxmox_provider_options(config: pulumi.Config) -> ProxmoxProviderOptions:
    """Create the Proxmox provider and resource options for the stack."""
    provider = create_proxmox_provider(config)
    return ProxmoxProviderOptions(
        component=pulumi.ResourceOptions(providers=[provider]),
        host_connection=create_proxmox_host_connection(config),
        resource=pulumi.ResourceOptions(provider=provider),
    )


def create_proxmox_provider(config: pulumi.Config) -> proxmoxve.Provider:
    """Create the configured Proxmox VE provider."""
    api_token = config.get_secret("proxmox_api_token")
    password = (
        None if api_token is not None else config.require_secret("proxmox_password")
    )
    return proxmoxve.Provider(
        "proxmox-provider",
        api_token=api_token,
        endpoint=config.require("proxmox_endpoint"),
        insecure=config.get_bool("proxmox_insecure", False),
        min_tls=config.get("proxmox_min_tls"),
        password=password,
        random_vm_id_end=config.get_int("proxmox_random_vm_id_end"),
        random_vm_id_start=config.get_int("proxmox_random_vm_id_start"),
        random_vm_ids=config.get_bool("proxmox_random_vm_ids"),
        ssh=proxmoxve.ProviderSshArgs(
            agent=config.get_bool("proxmox_ssh_agent", True),
            agent_forwarding=config.get_bool("proxmox_ssh_agent_forwarding"),
            agent_socket=config.get("proxmox_ssh_agent_socket"),
            node_address_source=config.get("proxmox_ssh_node_address_source"),
            password=config.get_secret("proxmox_ssh_password"),
            private_key=config.get_secret("proxmox_ssh_private_key"),
            username=config.require("proxmox_ssh_username"),
        ),
        tmp_dir=config.get("proxmox_tmp_dir"),
        username=config.require("proxmox_automation_user"),
    )


def create_proxmox_host_connection(config: pulumi.Config) -> ConnectionArgs:
    """Create an SSH connection for Proxmox host lifecycle commands."""
    ssh_password = config.get_secret("proxmox_ssh_password")
    if ssh_password is None:
        ssh_password = config.get_secret("proxmox_password")

    return ConnectionArgs(
        host=host_from_cidr(config.require("proxmox_node_cidr")),
        port=22,
        user=config.require("proxmox_ssh_username"),
        agent_socket_path=config.get("proxmox_ssh_agent_socket"),
        password=ssh_password,
        private_key=config.get_secret("proxmox_ssh_private_key"),
    )
