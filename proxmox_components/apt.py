"""Proxmox apt repository component."""

from __future__ import annotations

from dataclasses import dataclass

import pulumi
from pulumi_proxmoxve.apt.repository import Repository
from pulumi_proxmoxve.apt.standard.repository import Repository as StandardRepository

from .base import ComponentBase


@dataclass(frozen=True)
class AptRepositorySpec:
    """Single apt repository toggle managed on a node."""

    resource_name: str
    handle: str
    enabled: bool


APT_REPOSITORY_SPECS = [
    AptRepositorySpec("pve-no-subscription", "no-subscription", True),
    AptRepositorySpec("pve-enterprise", "enterprise", False),
    AptRepositorySpec("ceph-squid-no-subscription", "ceph-squid-no-subscription", True),
    AptRepositorySpec("ceph-squid-enterprise", "ceph-squid-enterprise", False),
]


class ProxmoxAptRepositories(ComponentBase):
    """Manage the node apt repository toggles."""

    def __init__(
        self,
        name: str,
        node_name: str,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        """Configure the node apt repositories."""
        super().__init__(name, opts=opts)

        for repository in APT_REPOSITORY_SPECS:
            standard = StandardRepository(
                f"{name}-{repository.resource_name}-source",
                handle=repository.handle,
                node=node_name,
                opts=pulumi.ResourceOptions(parent=self),
            )
            Repository(
                f"{name}-{repository.resource_name}-config",
                enabled=repository.enabled,
                file_path=standard.file_path,
                index=standard.index,
                node=standard.node,
                opts=pulumi.ResourceOptions(parent=self),
            )

        self.register_outputs({})
