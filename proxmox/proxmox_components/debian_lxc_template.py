"""Reusable Debian LXC base template component."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pulumi
import pulumi_random as random
import pulumi_tls as tls
from pulumi_proxmoxve._inputs import (
    ContainerLegacyConsoleArgs,
    ContainerLegacyCpuArgs,
    ContainerLegacyDiskArgs,
    ContainerLegacyFeaturesArgs,
    ContainerLegacyInitializationArgs,
    ContainerLegacyInitializationUserAccountArgs,
    ContainerLegacyMemoryArgs,
    ContainerLegacyOperatingSystemArgs,
)
from pulumi_proxmoxve.container_legacy import ContainerLegacy, ContainerLegacyArgs

from .base import ComponentBase

if TYPE_CHECKING:
    from .enums import Datastore


@dataclass(frozen=True)
class DebianLxcTemplateConfig:
    """Reusable Debian LXC template settings shared across workloads."""

    vm_id: int
    hostname: str
    description: str
    rootfs_datastore_id: Datastore
    rootfs_size_gb: int
    start_on_boot: bool
    started: bool
    unprivileged: bool
    nesting: bool
    tags: list[str]


class DebianLxcTemplate(ComponentBase):
    """Provision a generic Debian LXC template plus its SSH bootstrap materials."""

    ssh_private_key: pulumi.Output[str]
    vm_id: pulumi.Output[int]

    def __init__(
        self,
        name: str,
        *,
        node_name: str,
        image_file_id: pulumi.Input[str],
        settings: DebianLxcTemplateConfig,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        """Create the shared Debian LXC template and SSH bootstrap materials."""
        super().__init__(name, opts=opts)

        template_password = random.RandomPassword(
            f"{name}-password",
            length=20,
            special=True,
            min_lower=1,
            min_numeric=1,
            min_special=1,
            min_upper=1,
            override_special="!#$%?-_",
            opts=pulumi.ResourceOptions(parent=self),
        )
        ssh_key = tls.PrivateKey(
            f"{name}-ssh-key",
            algorithm="ED25519",
            opts=pulumi.ResourceOptions(parent=self),
        )

        template = ContainerLegacy(
            f"{name}-container",
            args=ContainerLegacyArgs(
                description=settings.description,
                node_name=node_name,
                console=ContainerLegacyConsoleArgs(enabled=True, tty_count=2),
                cpu=ContainerLegacyCpuArgs(architecture="amd64", cores=1, units=1024),
                features=ContainerLegacyFeaturesArgs(
                    fuse=False, keyctl=False, mounts=[], nesting=settings.nesting
                ),
                memory=ContainerLegacyMemoryArgs(dedicated=512, swap=0),
                start_on_boot=settings.start_on_boot,
                started=settings.started,
                tags=settings.tags,
                vm_id=settings.vm_id,
                template=True,
                initialization=ContainerLegacyInitializationArgs(
                    hostname=settings.hostname,
                    user_account=ContainerLegacyInitializationUserAccountArgs(
                        keys=[
                            pulumi.Output.from_input(ssh_key.public_key_openssh).apply(
                                str.strip
                            )
                        ],
                        password=template_password.result,
                    ),
                ),
                disk=ContainerLegacyDiskArgs(
                    datastore_id=settings.rootfs_datastore_id,
                    size=settings.rootfs_size_gb,
                ),
                network_interfaces=[],
                operating_system=ContainerLegacyOperatingSystemArgs(
                    template_file_id=image_file_id, type="debian"
                ),
                timeout_clone=1800,
                timeout_create=1800,
                timeout_delete=60,
                timeout_update=1800,
                unprivileged=settings.unprivileged,
            ),
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.ssh_private_key = ssh_key.private_key_openssh
        self.vm_id = template.vm_id
        self.register_outputs(
            {
                "ssh_private_key": self.ssh_private_key,
                "template_vm_id": self.vm_id,
            },
        )
