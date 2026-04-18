"""Foundation-level Proxmox resources shared by workloads."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pulumi

from .apt import ProxmoxAptRepositories
from .base import ComponentBase
from .network import ProxmoxNetwork
from .users import ProxmoxUsers

if TYPE_CHECKING:
    from .network import BridgeConfig, ProxmoxNodeConfig
    from .users import UserConfig


class HomelabFoundation(ComponentBase):
    """Provision the base Proxmox node resources used by all workloads."""

    def __init__(
        self,
        name: str,
        *,
        node: ProxmoxNodeConfig,
        bridges: list[BridgeConfig],
        users: list[UserConfig],
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        """Create the base node resources that workloads depend on."""
        super().__init__(name, opts=opts)

        network = ProxmoxNetwork(
            f"{name}-network",
            node_name=node.name,
            default_bridge_name=node.default_bridge_name,
            bridges=bridges,
            opts=pulumi.ResourceOptions(parent=self),
        )
        ProxmoxAptRepositories(
            f"{name}-apt",
            node_name=node.name,
            opts=pulumi.ResourceOptions(parent=self),
        )
        users_component = ProxmoxUsers(
            f"{name}-users",
            users=users,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.default_network_name = network.default_network_name
        self.generated_passwords = users_component.generated_passwords
        self.register_outputs(
            {
                "default_network_name": self.default_network_name,
                "generated_passwords": self.generated_passwords,
            },
        )
