"""AdGuard container component."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pulumi
import pulumi_random as random
from pulumi_command.remote import Command, ConnectionArgs
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

from .adguard_config_renderer import (
    BCRYPT_HASH_MARKER,
    CERTIFICATE_PATH,
    PRIVATE_KEY_PATH,
    render_adguard_config,
)
from .base import ComponentBase
from .helpers import format_resource_name, host_from_cidr

if TYPE_CHECKING:
    from .adguard_config_renderer import (
        AdGuardAllowRule,
        AdGuardDnsConfig,
        AdGuardFilteringConfig,
        AdGuardHttpConfig,
        AdGuardHttpDohConfig,
        AdGuardLogConfig,
        AdGuardTlsConfig,
        FilterListConfig,
    )
    from .enums import Datastore


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

    rootfs_datastore_id: Datastore
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


@dataclass(frozen=True)
class AdGuardConfig:
    """Typed settings for the AdGuard workload."""

    version: str
    admin_username: str
    http: AdGuardHttpConfig
    http_doh: AdGuardHttpDohConfig
    dns: AdGuardDnsConfig
    filtering: AdGuardFilteringConfig
    query_log: AdGuardLogConfig
    statistics: AdGuardLogConfig
    tls: AdGuardTlsConfig
    blocked_services: list[str]
    filter_lists: list[FilterListConfig]
    allow_rules: list[AdGuardAllowRule]
    user_rules: list[str]
    lxc_runtime: LxcRuntimeConfig
    instances: list[AdGuardInstanceConfig]


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


def _write_remote_file_command(path: str) -> str:
    parent = path.rsplit("/", maxsplit=1)[0]
    return (
        f"set -euo pipefail\ninstall -d -m 700 {parent}\ncat > {path}\nchmod 600 {path}"
    )


def _apply_password_hash_command(path: str) -> str:
    escaped_placeholder = json.dumps(BCRYPT_HASH_MARKER)
    return (
        "set -euo pipefail\n"
        "python3 -c '"
        "import sys; "
        "from pathlib import Path; "
        f"path = Path({json.dumps(path)}); "
        "data = path.read_text(); "
        'hash_value = sys.stdin.read().rstrip("\\n"); '
        f"placeholder = {escaped_placeholder}; "
        "path.write_text(data.replace(placeholder, hash_value, 1))"
        "'"
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


class AdGuardContainers(ComponentBase):
    """Manage AdGuard containers cloned from a reusable Debian LXC template."""

    def __init__(
        self,
        name: str,
        *,
        node_name: str,
        settings: AdGuardConfig,
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
        instances = settings.instances
        lxc_runtime = settings.lxc_runtime

        for instance in instances:
            instance_resource_name = format_resource_name(instance.hostname, self)
            rendered_config = render_adguard_config(
                username=settings.admin_username,
                server_name=instance.server_name,
                http=settings.http,
                http_doh=settings.http_doh,
                dns=settings.dns,
                filtering=settings.filtering,
                query_log=settings.query_log,
                statistics=settings.statistics,
                tls=settings.tls,
                blocked_services=settings.blocked_services,
                filter_lists=settings.filter_lists,
                allow_rules=settings.allow_rules,
                user_rules=settings.user_rules,
            )
            host = host_from_cidr(instance.ip_address)

            container_dependencies: list[pulumi.Resource] = []
            if previous_install is not None:
                container_dependencies.append(previous_install)

            container = ContainerLegacy(
                f"{name}-{instance_resource_name}",
                args=ContainerLegacyArgs(
                    description=f"Managed by Pulumi; AdGuardHome {instance.hostname}",
                    node_name=node_name,
                    console=ContainerLegacyConsoleArgs(enabled=True, tty_count=2),
                    cpu=ContainerLegacyCpuArgs(
                        architecture="amd64", cores=1, units=1024
                    ),
                    features=ContainerLegacyFeaturesArgs(
                        fuse=False,
                        keyctl=False,
                        mounts=[],
                        nesting=lxc_runtime.nesting,
                    ),
                    memory=ContainerLegacyMemoryArgs(dedicated=512, swap=0),
                    start_on_boot=lxc_runtime.start_on_boot,
                    started=lxc_runtime.started,
                    tags=lxc_runtime.tags,
                    vm_id=instance.vm_id,
                    clone=ContainerLegacyCloneArgs(vm_id=template_vm_id),
                    initialization=ContainerLegacyInitializationArgs(
                        hostname=instance.hostname,
                        ip_configs=[
                            ContainerLegacyInitializationIpConfigArgs(
                                ipv4=ContainerLegacyInitializationIpConfigIpv4Args(
                                    address=instance.ip_address,
                                    gateway=instance.gateway,
                                ),
                            ),
                        ],
                    ),
                    network_interfaces=[
                        ContainerLegacyNetworkInterfaceArgs(name=default_network_name),
                    ],
                    disk=ContainerLegacyDiskArgs(
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

            conn = _ssh_connection(host, ssh_connection_key)

            copy_config = Command(
                f"{name}-{instance_resource_name}-copy-config",
                connection=conn,
                create="mkdir -p /opt/AdGuardHome && cat > /opt/AdGuardHome/AdGuardHome.yaml",
                update="mkdir -p /opt/AdGuardHome && cat > /opt/AdGuardHome/AdGuardHome.yaml",
                stdin=rendered_config,
                triggers=[container_lifecycle, rendered_config],
                opts=pulumi.ResourceOptions(parent=container),
            )
            patch_password = Command(
                f"{name}-{instance_resource_name}-patch-password",
                connection=conn,
                create=_apply_password_hash_command(
                    "/opt/AdGuardHome/AdGuardHome.yaml"
                ),
                update=_apply_password_hash_command(
                    "/opt/AdGuardHome/AdGuardHome.yaml"
                ),
                stdin=admin_password.bcrypt_hash,
                triggers=[container_lifecycle, admin_password.bcrypt_hash],
                opts=pulumi.ResourceOptions(parent=container, depends_on=[copy_config]),
            )
            write_cert = Command(
                f"{name}-{instance_resource_name}-write-cert",
                connection=conn,
                create=_write_remote_file_command(CERTIFICATE_PATH),
                update=_write_remote_file_command(CERTIFICATE_PATH),
                stdin=certificate_pem,
                triggers=[container_lifecycle, certificate_pem],
                opts=pulumi.ResourceOptions(parent=container),
            )
            write_key = Command(
                f"{name}-{instance_resource_name}-write-key",
                connection=conn,
                create=_write_remote_file_command(PRIVATE_KEY_PATH),
                update=_write_remote_file_command(PRIVATE_KEY_PATH),
                stdin=private_key_pem,
                triggers=[container_lifecycle, private_key_pem],
                opts=pulumi.ResourceOptions(parent=container),
            )
            install_dependency = Command(
                f"{name}-{instance_resource_name}-install",
                connection=conn,
                create=_install_adguard_command(settings.version),
                triggers=[container_lifecycle],
                opts=pulumi.ResourceOptions(
                    parent=container,
                    depends_on=[patch_password, write_cert, write_key],
                ),
            )
            reload_config = Command(
                f"{name}-{instance_resource_name}-reload-config",
                connection=conn,
                triggers=[
                    container_lifecycle,
                    rendered_config,
                    admin_password.bcrypt_hash,
                    certificate_pem,
                    private_key_pem,
                ],
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
                    parent=container,
                    depends_on=[
                        patch_password,
                        write_cert,
                        write_key,
                        install_dependency,
                    ],
                ),
            )
            Command(
                f"{name}-{instance_resource_name}-update",
                connection=conn,
                triggers=[container_lifecycle, settings.version],
                create=_update_adguard_command(settings.version),
                update=_update_adguard_command(settings.version),
                opts=pulumi.ResourceOptions(
                    parent=container,
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
