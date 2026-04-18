"""Generic Proxmox VM components with OS-aware defaults."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

import pulumi

if TYPE_CHECKING:
    from collections.abc import Sequence

from pulumi_proxmoxve import FileLegacy, FileLegacySourceRawArgs
from pulumi_proxmoxve._inputs import (
    VmLegacyAgentArgs,
    VmLegacyAgentWaitForIpArgs,
    VmLegacyCdromArgs,
    VmLegacyCpuArgs,
    VmLegacyDiskArgs,
    VmLegacyEfiDiskArgs,
    VmLegacyInitializationArgs,
    VmLegacyInitializationDnsArgs,
    VmLegacyInitializationIpConfigArgs,
    VmLegacyInitializationIpConfigIpv4Args,
    VmLegacyMemoryArgs,
    VmLegacyNetworkDeviceArgs,
    VmLegacyOperatingSystemArgs,
)
from pulumi_proxmoxve.vm_legacy import VmLegacy, VmLegacyArgs

from .base import ComponentBase
from .enums import Datastore


class GuestOS(StrEnum):
    """Supported guest operating systems."""

    WIN11 = "win11"
    DEBIAN = "debian"
    UBUNTU = "ubuntu"


@dataclass(frozen=True)
class _OSProfile:
    """Internal OS-specific VM defaults derived from the guest OS choice."""

    os_type: str
    bios: str
    machine: str
    cpu_type: str
    scsi_hardware: str
    efi_type: str
    efi_pre_enrolled_keys: bool


_OS_PROFILES: dict[GuestOS, _OSProfile] = {
    GuestOS.WIN11: _OSProfile(
        os_type="win11",
        bios="ovmf",
        machine="pc-q35-10.1",
        cpu_type="x86-64-v2-AES",
        scsi_hardware="virtio-scsi-pci",
        efi_type="4m",
        efi_pre_enrolled_keys=True,
    ),
    GuestOS.DEBIAN: _OSProfile(
        os_type="l26",
        bios="ovmf",
        machine="pc-q35-10.1",
        cpu_type="host",
        scsi_hardware="virtio-scsi-single",
        efi_type="4m",
        efi_pre_enrolled_keys=False,
    ),
    GuestOS.UBUNTU: _OSProfile(
        os_type="l26",
        bios="ovmf",
        machine="pc-q35-10.1",
        cpu_type="host",
        scsi_hardware="virtio-scsi-single",
        efi_type="4m",
        efi_pre_enrolled_keys=False,
    ),
}


@dataclass(frozen=True)
class IsoAttachment:
    """An ISO image to attach to a VM."""

    file_id: pulumi.Input[str]
    interface: str


@dataclass(frozen=True)
class CloudInitNetworkConfig:
    """Static network configuration for cloud-init VMs."""

    address: str
    gateway: str
    dns_servers: list[str]
    dns_domain: str | None = None


class ProxmoxVm(ComponentBase):
    """Create a Proxmox VM with OS-aware defaults."""

    vm_id: pulumi.Output[int]

    def __init__(
        self,
        name: str,
        *,
        node_name: str,
        network_bridge: pulumi.Input[str],
        vm_name: str,
        os: GuestOS,
        isos: Sequence[IsoAttachment],
        cpu_cores: int = 2,
        memory_mb: int = 2048,
        disk_size_gb: int = 32,
        disk_datastore_id: Datastore = Datastore.LOCAL_LVM,
        vm_id: int | None = None,
        description: str = "",
        tags: list[str] | None = None,
        on_boot: bool = False,
        started: bool = False,
        stop_on_destroy: bool = True,
        pool_id: pulumi.Input[str] | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        """Create a VM with sane defaults derived from the guest OS."""
        super().__init__(name, opts=opts)

        profile = _OS_PROFILES[os]

        if not isos:
            msg = "At least one ISO attachment is required (install media)"
            raise ValueError(msg)

        cdrom = VmLegacyCdromArgs(
            file_id=isos[0].file_id,
            interface=isos[0].interface,
        )

        disks: list[VmLegacyDiskArgs] = [
            VmLegacyDiskArgs(
                file_id=iso.file_id,
                file_format="raw",
                interface=iso.interface,
            )
            for iso in isos[1:]
        ]
        disks.append(
            VmLegacyDiskArgs(
                datastore_id=disk_datastore_id,
                discard="on",
                file_format="raw",
                interface="scsi0",
                iothread=True,
                size=disk_size_gb,
                ssd=True,
            ),
        )

        ignore_changes = [f"disks[{i}].speed" for i in range(len(disks))]

        vm = VmLegacy(
            name,
            args=VmLegacyArgs(
                name=vm_name,
                node_name=node_name,
                vm_id=vm_id,
                pool_id=pool_id,
                tags=sorted(tags or []),
                description=description,
                stop_on_destroy=stop_on_destroy,
                machine=profile.machine,
                on_boot=on_boot,
                started=started,
                scsi_hardware=profile.scsi_hardware,
                bios=profile.bios,
                operating_system=VmLegacyOperatingSystemArgs(type=profile.os_type),
                cpu=VmLegacyCpuArgs(cores=cpu_cores, type=profile.cpu_type),
                agent=VmLegacyAgentArgs(enabled=True),
                memory=VmLegacyMemoryArgs(dedicated=memory_mb, floating=memory_mb // 2),
                network_devices=[
                    VmLegacyNetworkDeviceArgs(bridge=network_bridge),
                ],
                cdrom=cdrom,
                disks=disks,
                efi_disk=VmLegacyEfiDiskArgs(
                    datastore_id=disk_datastore_id,
                    file_format="raw",
                    pre_enrolled_keys=profile.efi_pre_enrolled_keys,
                    type=profile.efi_type,
                ),
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                ignore_changes=ignore_changes,
            ),
        )

        self.vm_id = vm.vm_id
        self.register_outputs({"vm_id": self.vm_id})


class ProxmoxCloudInitVm(ComponentBase):
    """Create a Linux VM from a cloud image with cloud-init bootstrap."""

    vm_id: pulumi.Output[int]
    mac_addresses: pulumi.Output[Sequence[str]]

    def __init__(
        self,
        name: str,
        *,
        node_name: str,
        network_bridge: pulumi.Input[str],
        vm_name: str,
        os: GuestOS,
        image_file_id: pulumi.Input[str],
        network: CloudInitNetworkConfig,
        user_data: pulumi.Input[str],
        cpu_cores: int = 2,
        memory_mb: int = 2048,
        disk_size_gb: int = 32,
        disk_datastore_id: Datastore = Datastore.LOCAL_LVM,
        vm_id: int | None = None,
        description: str = "",
        tags: list[str] | None = None,
        on_boot: bool = True,
        started: bool = True,
        stop_on_destroy: bool = True,
        pool_id: pulumi.Input[str] | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        """Create a cloud-init VM from a downloaded cloud image."""
        super().__init__(name, opts=opts)

        profile = _OS_PROFILES[os]

        snippet = FileLegacy(
            f"{name}-cloud-config",
            datastore_id=Datastore.LOCAL,
            node_name=node_name,
            content_type="snippets",
            overwrite=True,
            source_raw=FileLegacySourceRawArgs(
                data=user_data,
                file_name=f"{name}-cloud-config.yaml",
            ),
            opts=pulumi.ResourceOptions(parent=self),
        )

        vm = VmLegacy(
            name,
            args=VmLegacyArgs(
                name=vm_name,
                node_name=node_name,
                vm_id=vm_id,
                pool_id=pool_id,
                tags=sorted(tags or []),
                description=description,
                stop_on_destroy=stop_on_destroy,
                machine=profile.machine,
                on_boot=on_boot,
                started=started,
                scsi_hardware=profile.scsi_hardware,
                bios=profile.bios,
                operating_system=VmLegacyOperatingSystemArgs(type=profile.os_type),
                cpu=VmLegacyCpuArgs(cores=cpu_cores, type=profile.cpu_type),
                agent=VmLegacyAgentArgs(
                    enabled=True,
                    trim=True,
                    type="virtio",
                    timeout="5m",
                    wait_for_ip=VmLegacyAgentWaitForIpArgs(ipv4=True),
                ),
                memory=VmLegacyMemoryArgs(dedicated=memory_mb, floating=memory_mb // 2),
                network_devices=[VmLegacyNetworkDeviceArgs(bridge=network_bridge)],
                initialization=VmLegacyInitializationArgs(
                    datastore_id=disk_datastore_id,
                    interface="ide2",
                    type="nocloud",
                    dns=VmLegacyInitializationDnsArgs(
                        domain=network.dns_domain,
                        servers=network.dns_servers,
                    ),
                    ip_configs=[
                        VmLegacyInitializationIpConfigArgs(
                            ipv4=VmLegacyInitializationIpConfigIpv4Args(
                                address=network.address,
                                gateway=network.gateway,
                            ),
                        )
                    ],
                    user_data_file_id=snippet.id,
                ),
                boot_orders=["scsi0", "net0"],
                cdrom=VmLegacyCdromArgs(file_id="none"),
                disks=[
                    VmLegacyDiskArgs(
                        datastore_id=disk_datastore_id,
                        discard="on",
                        import_from=image_file_id,
                        interface="scsi0",
                        iothread=True,
                        size=disk_size_gb,
                        ssd=True,
                    ),
                ],
                efi_disk=VmLegacyEfiDiskArgs(
                    datastore_id=disk_datastore_id,
                    file_format="raw",
                    pre_enrolled_keys=profile.efi_pre_enrolled_keys,
                    type=profile.efi_type,
                ),
                timeout_create=600,
                timeout_start_vm=300,
                reboot_after_update=False,
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                ignore_changes=["disks[0].speed"],
            ),
        )

        self.vm_id = vm.vm_id
        self.mac_addresses = vm.mac_addresses
        self.register_outputs(
            {"vm_id": self.vm_id, "mac_addresses": self.mac_addresses}
        )
