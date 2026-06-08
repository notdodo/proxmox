"""Generic Proxmox VM components with OS-aware defaults."""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from enum import StrEnum
from functools import partial
from typing import TYPE_CHECKING, Any, cast

import pulumi
from pulumi_command.remote import Command, ConnectionArgs

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
    VmLegacyTpmStateArgs,
)
from pulumi_proxmoxve.vm_legacy import VmLegacy, VmLegacyArgs

from .base import ComponentBase
from .enums import Datastore
from .performance import VmPerformanceConfig

CDROM_INTERFACE_RE = re.compile(r"^(ide|sata|scsi)(\d+)$")
Q35_IDE_CDROM_INTERFACES = {"ide0", "ide2"}


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
    tpm_version: str | None = None


OS_PROFILES: dict[GuestOS, _OSProfile] = {
    GuestOS.WIN11: _OSProfile(
        os_type="win11",
        bios="ovmf",
        machine="pc-q35-10.1",
        cpu_type="x86-64-v2-AES",
        scsi_hardware="virtio-scsi-single",
        efi_type="4m",
        efi_pre_enrolled_keys=True,
        tpm_version="v2.0",
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


def _validate_iso_attachments(
    isos: Sequence[IsoAttachment],
    profile: _OSProfile,
) -> None:
    seen_interfaces: set[str] = set()
    for iso in isos:
        match = CDROM_INTERFACE_RE.match(iso.interface)
        if not match:
            msg = f"Invalid ISO interface {iso.interface!r}; use ideN, sataN, or scsiN."
            raise ValueError(msg)
        if iso.interface in seen_interfaces:
            msg = f"Duplicate ISO interface {iso.interface!r}."
            raise ValueError(msg)
        seen_interfaces.add(iso.interface)
        if (
            profile.machine.startswith("pc-q35")
            and match.group(1) == "ide"
            and iso.interface not in Q35_IDE_CDROM_INTERFACES
        ):
            msg = (
                f"Invalid q35 IDE CD-ROM interface {iso.interface!r}; "
                "use ide0/ide2 or a sataN/scsiN CD-ROM interface."
            )
            raise ValueError(msg)


def _qm_set_cdrom_command(
    vm_id: int,
    interface: str,
    file_id: str,
) -> str:
    vmid = shlex.quote(str(vm_id))
    return "\n".join(
        [
            "set -euo pipefail",
            f"qm set {vmid} --{interface} {shlex.quote(f'file={file_id},media=cdrom')}",
        ]
    )


def _qm_delete_drive_command(vm_id: int, interface: str) -> str:
    vmid = shlex.quote(str(vm_id))
    return "\n".join(
        ["set -euo pipefail", _qm_delete_drive_if_set_line(vmid, interface)]
    )


def _qm_delete_drive_if_set_line(vmid: str, interface: str) -> str:
    config_key_pattern = shlex.quote(f"^{interface}:")
    return (
        f"if qm config {vmid} | grep -q {config_key_pattern}; "
        f"then qm set {vmid} -delete {interface}; fi"
    )


def _render_qm_set_cdrom_command(
    values: Sequence[Any],
    interface: str,
) -> str:
    return _qm_set_cdrom_command(
        cast("int", values[0]),
        interface,
        cast("str", values[1]),
    )


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
        performance: VmPerformanceConfig | None = None,
        proxmox_host_connection: ConnectionArgs | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        """Create a VM with sane defaults derived from the guest OS."""
        super().__init__(name, opts=opts)

        profile = OS_PROFILES[os]
        performance = performance or VmPerformanceConfig()

        if not isos:
            msg = "At least one ISO attachment is required (install media)"
            raise ValueError(msg)
        _validate_iso_attachments(isos, profile)
        if len(isos) > 1 and proxmox_host_connection is None:
            msg = (
                "Secondary ISO attachments require a Proxmox host SSH connection "
                "because the stable proxmoxve VmLegacy resource only supports one "
                "provider-managed CD-ROM."
            )
            raise ValueError(msg)
        if len(isos) > 1 and started:
            msg = (
                "VMs with secondary ISO attachments must be created with started=False "
                "so all install media is attached before the guest boots."
            )
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
                aio=performance.disk_aio,
                backup=performance.disk_backup,
                cache=performance.disk_cache,
                discard="on",
                file_format="raw",
                interface="scsi0",
                iothread=True,
                replicate=performance.disk_replicate,
                size=disk_size_gb,
                ssd=True,
            ),
        )

        system_disk_index = len(disks) - 1
        ignore_changes = [
            *(f"disks[{i}]" for i in range(system_disk_index)),
            f"disks[{system_disk_index}].speed",
        ]

        tpm_state = (
            VmLegacyTpmStateArgs(
                datastore_id=disk_datastore_id,
                version=profile.tpm_version,
            )
            if profile.tpm_version is not None
            else None
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
                boot_orders=[isos[0].interface, "scsi0", "net0"],
                operating_system=VmLegacyOperatingSystemArgs(type=profile.os_type),
                cpu=VmLegacyCpuArgs(
                    cores=cpu_cores,
                    limit=performance.cpu_limit,
                    type=profile.cpu_type,
                    units=performance.cpu_units,
                ),
                agent=VmLegacyAgentArgs(
                    enabled=True,
                    timeout="5m",
                    trim=True,
                    type="virtio",
                ),
                memory=VmLegacyMemoryArgs(dedicated=memory_mb, floating=memory_mb),
                network_devices=[
                    VmLegacyNetworkDeviceArgs(
                        bridge=network_bridge,
                        model="virtio",
                        mtu=performance.network_mtu,
                        queues=performance.network_queues,
                    ),
                ],
                cdrom=cdrom,
                disks=disks,
                efi_disk=VmLegacyEfiDiskArgs(
                    datastore_id=disk_datastore_id,
                    file_format="raw",
                    pre_enrolled_keys=profile.efi_pre_enrolled_keys,
                    type=profile.efi_type,
                ),
                tpm_state=tpm_state,
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                ignore_changes=ignore_changes,
            ),
        )

        for iso in isos[1:]:
            if proxmox_host_connection is None:
                msg = "Secondary ISO attachment connection was not configured."
                raise RuntimeError(msg)
            command = pulumi.Output.all(vm.vm_id, iso.file_id).apply(
                partial(
                    _render_qm_set_cdrom_command,
                    interface=iso.interface,
                )
            )
            delete = vm.vm_id.apply(
                partial(_qm_delete_drive_command, interface=iso.interface)
            )
            Command(
                f"{name}-{iso.interface}-cdrom",
                connection=proxmox_host_connection,
                create=command,
                update=command,
                delete=delete,
                triggers=[vm.vm_id, iso.file_id, iso.interface],
                opts=pulumi.ResourceOptions(parent=vm, depends_on=[vm]),
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
        performance: VmPerformanceConfig | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        """Create a cloud-init VM from a downloaded cloud image."""
        super().__init__(name, opts=opts)

        profile = OS_PROFILES[os]
        performance = performance or VmPerformanceConfig()

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
                cpu=VmLegacyCpuArgs(
                    cores=cpu_cores,
                    limit=performance.cpu_limit,
                    type=profile.cpu_type,
                    units=performance.cpu_units,
                ),
                agent=VmLegacyAgentArgs(
                    enabled=True,
                    trim=True,
                    type="virtio",
                    timeout="5m",
                    wait_for_ip=VmLegacyAgentWaitForIpArgs(ipv4=True),
                ),
                memory=VmLegacyMemoryArgs(dedicated=memory_mb, floating=memory_mb),
                network_devices=[
                    VmLegacyNetworkDeviceArgs(
                        bridge=network_bridge,
                        model="virtio",
                        mtu=performance.network_mtu,
                        queues=performance.network_queues,
                    )
                ],
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
                        aio=performance.disk_aio,
                        backup=performance.disk_backup,
                        cache=performance.disk_cache,
                        discard="on",
                        import_from=image_file_id,
                        interface="scsi0",
                        iothread=True,
                        replicate=performance.disk_replicate,
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
