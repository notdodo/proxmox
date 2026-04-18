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


@dataclass(frozen=True)
class BridgeConfig:
    """Single managed Linux bridge definition."""

    resource_name: str
    name: str
    address: str
    gateway: str | None = None
    uplink_ports: list[str] | None = None
    autostart: bool = True
    comment: str = "Managed by Pulumi; Linux bridge"
    import_id: str | None = None


class ProxmoxNetwork(ComponentBase):
    """Manage the Linux bridge resources used by the homelab."""

    def __init__(
        self,
        name: str,
        node_name: str,
        default_bridge_name: str,
        bridges: list[BridgeConfig],
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        """Create the managed Linux bridge resources."""
        super().__init__(name, opts=opts)

        bridge_resources: dict[str, Bridge] = {}
        for bridge in bridges:
            bridge_resources[bridge.name] = Bridge(
                f"{name}-{bridge.resource_name}",
                node_name=node_name,
                name=bridge.name,
                address=bridge.address,
                gateway=bridge.gateway,
                autostart=bridge.autostart,
                comment=bridge.comment,
                ports=bridge.uplink_ports or [],
                opts=pulumi.ResourceOptions(
                    parent=self,
                    import_=bridge.import_id,
                ),
            )

        default_network = bridge_resources[default_bridge_name]
        self.default_network_name = default_network.name
        self.register_outputs(
            {
                "default_network_name": self.default_network_name,
            }
        )
