"""AdGuard container component."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pulumi
import pulumi_random as random
from pulumi_command.remote import Command, ConnectionArgs
from pulumi_proxmoxve._inputs import (
    ContainerLegacyCloneArgs as ContainerCloneArgs,
)
from pulumi_proxmoxve._inputs import (
    ContainerLegacyConsoleArgs as ContainerConsoleArgs,
)
from pulumi_proxmoxve._inputs import (
    ContainerLegacyCpuArgs as ContainerCpuArgs,
)
from pulumi_proxmoxve._inputs import (
    ContainerLegacyDiskArgs as ContainerDiskArgs,
)
from pulumi_proxmoxve._inputs import (
    ContainerLegacyFeaturesArgs as ContainerFeaturesArgs,
)
from pulumi_proxmoxve._inputs import (
    ContainerLegacyInitializationArgs as ContainerInitializationArgs,
)
from pulumi_proxmoxve._inputs import (
    ContainerLegacyInitializationIpConfigArgs as ContainerIpConfigArgs,
)
from pulumi_proxmoxve._inputs import (
    ContainerLegacyInitializationIpConfigIpv4Args as ContainerIpv4Args,
)
from pulumi_proxmoxve._inputs import (
    ContainerLegacyMemoryArgs as ContainerMemoryArgs,
)
from pulumi_proxmoxve._inputs import (
    ContainerLegacyNetworkInterfaceArgs as ContainerNetworkInterfaceArgs,
)
from pulumi_proxmoxve.container_legacy import ContainerLegacy as Container
from pulumi_proxmoxve.container_legacy import ContainerLegacyArgs as ContainerArgs

from .adguard_config_renderer import render_adguard_config
from .base import ComponentBase
from .helpers import format_resource_name

if TYPE_CHECKING:
    from .adguard_config_renderer import (
        AdGuardDnsConfig,
        AdGuardFilteringConfig,
        AdGuardHttpConfig,
        AdGuardLogConfig,
        AdGuardTlsConfig,
        FilterListConfig,
    )


@dataclass(frozen=True)
class AdGuardInstanceConfig:
    """Single AdGuard container instance."""

    hostname: str
    server_name: str
    vm_id: int
    ip_address: str
    gateway: str


@dataclass(frozen=True)
class LxcRuntimeConfig:
    """Reusable runtime policy for workload LXCs."""

    rootfs_datastore_id: str
    rootfs_size_gb: int
    start_on_boot: bool
    started: bool
    unprivileged: bool
    nesting: bool
    tags: list[str]
    timeout_clone: int
    timeout_create: int
    timeout_delete: int
    timeout_update: int


def _ssh_connection(host: str, private_key: pulumi.Input[str]) -> ConnectionArgs:
    return ConnectionArgs(
        host=host,
        port=22,
        user="root",
        private_key=private_key,
    )


def _adguard_archive_url(version: str) -> str:
    return (
        f"https://github.com/AdguardTeam/AdGuardHome/releases/download/"
        f"{version}/AdGuardHome_linux_amd64.tar.gz"
    )


def _apt_upgrade_commands() -> str:
    return (
        "export DEBIAN_FRONTEND=noninteractive\n"
        "apt-get update\n"
        "apt-get full-upgrade -y\n"
    )


def _reboot_if_required_command() -> str:
    return (
        "if [ -f /var/run/reboot-required ]; then\n"
        "  nohup sh -c 'sleep 2; systemctl reboot' >/dev/null 2>&1 &\n"
        "fi"
    )


def _install_adguard_command(version: str) -> str:
    archive_url = _adguard_archive_url(version)
    return (
        "mkdir -p /opt/AdGuardHome\n"
        f"{_apt_upgrade_commands()}"
        "apt-get install -y ca-certificates curl iproute2 tar\n"
        f"curl -fsSL -o /tmp/AdGuardHome_linux_amd64.tar.gz {archive_url}\n"
        "tar -C /opt -xzf /tmp/AdGuardHome_linux_amd64.tar.gz\n"
        "cd /opt/AdGuardHome\n"
        "./AdGuardHome -s install\n"
        "systemctl enable --now AdGuardHome"
    )


def _update_adguard_command(version: str) -> str:
    archive_url = _adguard_archive_url(version)
    return (
        f"{_apt_upgrade_commands()}"
        f"curl -fsSL -o /tmp/AdGuardHome_linux_amd64.tar.gz {archive_url}\n"
        "tar -C /opt -xzf /tmp/AdGuardHome_linux_amd64.tar.gz\n"
        "systemctl restart AdGuardHome\n"
        f"{_reboot_if_required_command()}"
    )


def _instance_host(ip_address: str) -> str:
    return ip_address.split("/", maxsplit=1)[0]


class AdGuardContainers(ComponentBase):
    """Manage AdGuard containers cloned from a reusable Debian LXC template."""

    def __init__(
        self,
        name: str,
        *,
        node_name: str,
        version: str,
        admin_username: str,
        http: AdGuardHttpConfig,
        dns: AdGuardDnsConfig,
        filtering: AdGuardFilteringConfig,
        query_log: AdGuardLogConfig,
        statistics: AdGuardLogConfig,
        tls: AdGuardTlsConfig,
        blocked_services: list[str],
        filter_lists: list[FilterListConfig],
        user_rules: list[str],
        lxc_runtime: LxcRuntimeConfig,
        instances: list[AdGuardInstanceConfig],
        template_vm_id: pulumi.Input[int],
        ssh_private_key: pulumi.Input[str],
        default_network_name: pulumi.Input[str],
        certificate_pem: pulumi.Input[str],
        private_key_pem: pulumi.Input[str],
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        """Create the AdGuard containers and their in-guest provisioning steps."""
        super().__init__(name, opts=opts)
        ssh_connection_key = pulumi.Output.from_input(ssh_private_key)
        admin_password = random.RandomPassword(
            f"{name}-admin-password",
            length=24,
            special=True,
            min_lower=1,
            min_numeric=1,
            min_special=1,
            min_upper=1,
            override_special="!#$%?-_",
            opts=pulumi.ResourceOptions(parent=self),
        )

        instance_vm_ids: dict[str, pulumi.Output[int]] = {}
        previous_install: pulumi.Resource | None = None

        for instance in instances:
            instance_resource_name = format_resource_name(instance.hostname, self)
            rendered_config = render_adguard_config(
                username=admin_username,
                password_bcrypt=admin_password.bcrypt_hash,
                server_name=instance.server_name,
                http=http,
                dns=dns,
                filtering=filtering,
                query_log=query_log,
                statistics=statistics,
                tls=tls,
                blocked_services=blocked_services,
                filter_lists=filter_lists,
                user_rules=user_rules,
                cert_pem=certificate_pem,
                private_key_pem=private_key_pem,
            )
            host = _instance_host(instance.ip_address)

            container_dependencies: list[pulumi.Resource] = []
            if previous_install is not None:
                container_dependencies.append(previous_install)

            container = Container(
                f"{name}-{instance_resource_name}",
                args=ContainerArgs(
                    description=f"AdGuardHome {instance.hostname}",
                    node_name=node_name,
                    console=ContainerConsoleArgs(enabled=True, tty_count=2),
                    cpu=ContainerCpuArgs(architecture="amd64", cores=1, units=1024),
                    features=ContainerFeaturesArgs(
                        fuse=False, keyctl=False, mounts=[], nesting=lxc_runtime.nesting
                    ),
                    memory=ContainerMemoryArgs(dedicated=512, swap=0),
                    start_on_boot=lxc_runtime.start_on_boot,
                    started=lxc_runtime.started,
                    tags=lxc_runtime.tags,
                    vm_id=instance.vm_id,
                    clone=ContainerCloneArgs(vm_id=template_vm_id),
                    initialization=ContainerInitializationArgs(
                        hostname=instance.hostname,
                        ip_configs=[
                            ContainerIpConfigArgs(
                                ipv4=ContainerIpv4Args(
                                    address=instance.ip_address,
                                    gateway=instance.gateway,
                                ),
                            ),
                        ],
                    ),
                    network_interfaces=[
                        ContainerNetworkInterfaceArgs(name=default_network_name),
                    ],
                    disk=ContainerDiskArgs(
                        datastore_id=lxc_runtime.rootfs_datastore_id,
                        size=lxc_runtime.rootfs_size_gb,
                    ),
                    timeout_clone=lxc_runtime.timeout_clone,
                    timeout_create=lxc_runtime.timeout_create,
                    timeout_delete=lxc_runtime.timeout_delete,
                    timeout_update=lxc_runtime.timeout_update,
                    unprivileged=lxc_runtime.unprivileged,
                ),
                opts=pulumi.ResourceOptions(
                    parent=self,
                    depends_on=container_dependencies,
                ),
            )
            container_lifecycle = pulumi.Output.all(
                container.id,
                container.ipv6,
                container.network_interfaces,
            ).apply(json.dumps)

            copy_config = Command(
                f"{name}-{instance_resource_name}-copy-config",
                connection=_ssh_connection(host, ssh_connection_key),
                create="mkdir -p /opt/AdGuardHome && cat > /opt/AdGuardHome/AdGuardHome.yaml",
                update="mkdir -p /opt/AdGuardHome && cat > /opt/AdGuardHome/AdGuardHome.yaml",
                stdin=rendered_config,
                triggers=[container_lifecycle, rendered_config],
                opts=pulumi.ResourceOptions(parent=self, depends_on=[container]),
            )
            install_dependency = Command(
                f"{name}-{instance_resource_name}-install",
                connection=_ssh_connection(host, ssh_connection_key),
                create=_install_adguard_command(version),
                triggers=[container_lifecycle],
                opts=pulumi.ResourceOptions(parent=self, depends_on=[copy_config]),
            )
            reload_config = Command(
                f"{name}-{instance_resource_name}-reload-config",
                connection=_ssh_connection(host, ssh_connection_key),
                triggers=[container_lifecycle, rendered_config],
                create=(
                    "if systemctl list-unit-files AdGuardHome.service >/dev/null 2>&1; then\n"
                    "  systemctl restart AdGuardHome\n"
                    "fi"
                ),
                update=(
                    "if systemctl list-unit-files AdGuardHome.service >/dev/null 2>&1; then\n"
                    "  systemctl restart AdGuardHome\n"
                    "fi"
                ),
                opts=pulumi.ResourceOptions(
                    parent=self,
                    depends_on=[copy_config, install_dependency],
                ),
            )
            Command(
                f"{name}-{instance_resource_name}-update",
                connection=_ssh_connection(host, ssh_connection_key),
                triggers=[container_lifecycle, version],
                create=_update_adguard_command(version),
                update=_update_adguard_command(version),
                opts=pulumi.ResourceOptions(
                    parent=self,
                    depends_on=[install_dependency, reload_config],
                ),
            )

            previous_install = install_dependency
            instance_vm_ids[instance_resource_name] = container.vm_id

        self.register_outputs(
            {
                "instance_vm_ids": instance_vm_ids,
            },
        )
