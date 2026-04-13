"""Foundation-level Proxmox resources shared by workloads."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pulumi

from .apt import ProxmoxAptRepositories
from .base import ComponentBase
from .debian_lxc_template import DebianLxcTemplate
from .network import ProxmoxNetwork
from .users import ProxmoxUsers

if TYPE_CHECKING:
    from .debian_lxc_template import DebianLxcTemplateConfig
    from .network import ProxmoxNodeConfig
    from .users import UserConfig


class HomelabFoundation(ComponentBase):
    """Provision the base Proxmox node resources used by all workloads."""

    def __init__(
        self,
        name: str,
        *,
        node: ProxmoxNodeConfig,
        users: list[UserConfig],
        lxc_template: DebianLxcTemplateConfig,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        """Create the base node resources that workloads depend on."""
        super().__init__(name, opts=opts)

        network = ProxmoxNetwork(
            f"{name}-network",
            settings=node,
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
        lxc_template_component = DebianLxcTemplate(
            f"{name}-debian-lxc-template",
            node_name=node.name,
            settings=lxc_template,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.default_network_name = network.default_network_name
        self.generated_passwords = users_component.generated_passwords
        self.lxc_template_vm_id = lxc_template_component.vm_id
        self.lxc_template_ssh_private_key = lxc_template_component.ssh_private_key
        self.register_outputs(
            {
                "default_network_name": self.default_network_name,
                "generated_passwords": self.generated_passwords,
                "lxc_template_vm_id": self.lxc_template_vm_id,
                "lxc_template_ssh_private_key": self.lxc_template_ssh_private_key,
            },
        )
