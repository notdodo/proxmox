"""Proxmox network component."""

from __future__ import annotations

from dataclasses import dataclass

import pulumi
from pulumi_proxmoxve.network.linux.bridge import Bridge

from .base import ComponentBase


@dataclass(frozen=True)
class ProxmoxNodeConfig:
    """Physical Proxmox node settings shared by multiple workloads."""

    name: str
    management_cidr: str
    default_bridge_name: str
    default_gateway: str
    uplink_ports: list[str]


class ProxmoxNetwork(ComponentBase):
    """Manage the Linux bridge resources used by the homelab."""

    def __init__(
        self,
        name: str,
        settings: ProxmoxNodeConfig,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        """Create the managed Linux bridge resources."""
        super().__init__(name, opts=opts)

        default_network = Bridge(
            f"{name}-default",
            node_name=settings.name,
            name=settings.default_bridge_name,
            address=settings.management_cidr,
            gateway=settings.default_gateway,
            autostart=True,
            comment="Managed by Pulumi",
            ports=settings.uplink_ports,
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        self.default_network_name = default_network.name
        self.register_outputs({"default_network_name": self.default_network_name})
