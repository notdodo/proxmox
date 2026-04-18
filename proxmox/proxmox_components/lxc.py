"""Generic Proxmox LXC container component cloned from a template."""

from __future__ import annotations

import pulumi
from pulumi_proxmoxve._inputs import (
    ContainerLegacyCloneArgs,
    ContainerLegacyConsoleArgs,
    ContainerLegacyCpuArgs,
    ContainerLegacyDiskArgs,
    ContainerLegacyFeaturesArgs,
    ContainerLegacyInitializationArgs,
    ContainerLegacyInitializationIpConfigArgs,
    ContainerLegacyInitializationIpConfigIpv4Args,
    ContainerLegacyMemoryArgs,
    ContainerLegacyNetworkInterfaceArgs,
)
from pulumi_proxmoxve.container_legacy import ContainerLegacy, ContainerLegacyArgs

from .base import ComponentBase
from .enums import Datastore


class ProxmoxLxc(ComponentBase):
    """Clone a Proxmox LXC container from a template with sane defaults."""

    vm_id: pulumi.Output[int]

    def __init__(
        self,
        name: str,
        *,
        node_name: str,
        network_bridge: pulumi.Input[str],
        template_vm_id: pulumi.Input[int],
        hostname: str,
        ip_address: str,
        gateway: str,
        vm_id: int | None = None,
        cpu_cores: int = 1,
        memory_mb: int = 512,
        disk_size_gb: int = 2,
        disk_datastore_id: Datastore = Datastore.LOCAL_LVM,
        start_on_boot: bool = True,
        started: bool = True,
        unprivileged: bool = True,
        nesting: bool = True,
        tags: list[str] | None = None,
        description: str = "",
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        """Create an LXC container cloned from a template."""
        super().__init__(name, opts=opts)

        container = ContainerLegacy(
            f"{name}-container",
            args=ContainerLegacyArgs(
                description=description,
                node_name=node_name,
                vm_id=vm_id,
                clone=ContainerLegacyCloneArgs(vm_id=template_vm_id),
                console=ContainerLegacyConsoleArgs(enabled=True, tty_count=2),
                cpu=ContainerLegacyCpuArgs(
                    architecture="amd64", cores=cpu_cores, units=1024
                ),
                features=ContainerLegacyFeaturesArgs(
                    fuse=False, keyctl=False, mounts=[], nesting=nesting
                ),
                memory=ContainerLegacyMemoryArgs(dedicated=memory_mb, swap=0),
                initialization=ContainerLegacyInitializationArgs(
                    hostname=hostname,
                    ip_configs=[
                        ContainerLegacyInitializationIpConfigArgs(
                            ipv4=ContainerLegacyInitializationIpConfigIpv4Args(
                                address=ip_address,
                                gateway=gateway,
                            ),
                        ),
                    ],
                ),
                network_interfaces=[
                    ContainerLegacyNetworkInterfaceArgs(name=network_bridge),
                ],
                disk=ContainerLegacyDiskArgs(
                    datastore_id=disk_datastore_id,
                    size=disk_size_gb,
                ),
                start_on_boot=start_on_boot,
                started=started,
                tags=sorted(tags or []),
                unprivileged=unprivileged,
                timeout_clone=1800,
                timeout_create=1800,
                timeout_delete=60,
                timeout_update=1800,
            ),
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.vm_id = container.vm_id
        self.register_outputs({"vm_id": self.vm_id})
