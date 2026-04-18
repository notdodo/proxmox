"""Portainer VM component."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from string import Template
from typing import TYPE_CHECKING

import pulumi
import pulumi_random as random
import pulumi_tls as tls
from pulumi_command.remote import Command, ConnectionArgs

from .base import ComponentBase
from .helpers import format_resource_name, host_from_cidr
from .vm import CloudInitNetworkConfig, GuestOS, ProxmoxCloudInitVm

if TYPE_CHECKING:
    from .enums import Datastore

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "files" / "templates"
_CLOUD_INIT_TEMPLATE = Template(
    (_TEMPLATES_DIR / "portainer-cloud-init.yml").read_text()
)
_COMPOSE_TEMPLATE = Template((_TEMPLATES_DIR / "portainer-compose.yml").read_text())


@dataclass(frozen=True)
class PortainerVmConfig:
    """Typed configuration for a Portainer VM."""

    vm_id: int
    vm_name: str
    hostname: str
    fqdn: str
    ip_address: str
    gateway: str
    dns_servers: list[str]
    disk_datastore_id: Datastore
    pool_id: pulumi.Input[str] | None = None
    admin_username: str = "admin"
    ssh_username: str = "ubuntu"
    cpu_cores: int = 2
    memory_mb: int = 4096
    disk_size_gb: int = 32
    public_port: int = 9443
    version: str = "lts"
    tags: list[str] = field(
        default_factory=lambda: ["docker", "portainer", "ubuntu", "vm"]
    )


@dataclass(frozen=True)
class _PortainerAuthPayload:
    """Payload used for Portainer API authentication endpoints."""

    Username: str
    Password: str


def _render_cloud_config(
    hostname: str,
    username: str,
    ssh_public_key: pulumi.Input[str],
) -> pulumi.Output[str]:
    return pulumi.Output.from_input(ssh_public_key).apply(
        lambda key: _CLOUD_INIT_TEMPLATE.safe_substitute(
            hostname=hostname,
            username=username,
            ssh_public_key=key.strip(),
        )
    )


def _render_compose(version: str, public_port: int) -> str:
    return _COMPOSE_TEMPLATE.safe_substitute(
        version=version,
        public_port=public_port,
    )


def _write_remote_file(path: str) -> str:
    parent = path.rsplit("/", maxsplit=1)[0]
    return (
        "set -euo pipefail\n"
        f"sudo install -d -m 700 {parent}\n"
        f"sudo cat > /tmp/_pulumi_file && sudo mv /tmp/_pulumi_file {path}\n"
        f"sudo chmod 600 {path}"
    )


_DEPLOY_COMMAND = (
    "set -euo pipefail\n"
    "sudo docker compose -f /opt/portainer/compose.yaml down -v 2>/dev/null || true\n"
    "sudo docker compose -f /opt/portainer/compose.yaml pull\n"
    "sudo docker compose -f /opt/portainer/compose.yaml up -d --remove-orphans"
)

_INIT_ADMIN_COMMAND = (
    "set -euo pipefail\n"
    "elapsed=0\n"
    "until curl -skf https://127.0.0.1:9443/api/status >/dev/null; do\n"
    "  sleep 5\n"
    "  elapsed=$((elapsed + 5))\n"
    '  [ "$elapsed" -ge 300 ] '
    '&& echo "Portainer did not start within 300s" >&2 && exit 1\n'
    "done\n"
    "curl -skf -H 'Content-Type: application/json' -d @- "
    "https://127.0.0.1:9443/api/users/admin/init"
)


class PortainerVm(ComponentBase):
    """Provision a cloud-init Ubuntu VM and bootstrap Portainer with TLS."""

    admin_username: pulumi.Output[str]
    admin_password: pulumi.Output[str]
    ssh_private_key: pulumi.Output[str]
    url: pulumi.Output[str]
    vm_id: pulumi.Output[int]

    def __init__(
        self,
        name: str,
        *,
        node_name: str,
        network_bridge: pulumi.Input[str],
        image_file_id: pulumi.Input[str],
        certificate_pem: pulumi.Input[str],
        issuer_pem: pulumi.Input[str],
        private_key_pem: pulumi.Input[str],
        settings: PortainerVmConfig,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        """Create the Portainer VM and bootstrap the service."""
        super().__init__(name, opts=opts)

        rn = format_resource_name(settings.hostname, self)
        child_opts = pulumi.ResourceOptions(parent=self)

        ssh_key = tls.PrivateKey(
            f"{name}-{rn}-ssh-key",
            algorithm="ED25519",
            opts=child_opts,
        )
        admin_password = random.RandomPassword(
            f"{name}-{rn}-admin-password",
            length=24,
            special=True,
            min_lower=1,
            min_numeric=1,
            min_special=1,
            min_upper=1,
            override_special="!#$%?-_",
            opts=child_opts,
        )

        vm = ProxmoxCloudInitVm(
            f"{name}-{rn}-vm",
            node_name=node_name,
            network_bridge=network_bridge,
            vm_name=settings.vm_name,
            os=GuestOS.UBUNTU,
            image_file_id=image_file_id,
            network=CloudInitNetworkConfig(
                address=settings.ip_address,
                gateway=settings.gateway,
                dns_servers=settings.dns_servers,
            ),
            user_data=_render_cloud_config(
                hostname=settings.hostname,
                username=settings.ssh_username,
                ssh_public_key=ssh_key.public_key_openssh,
            ),
            cpu_cores=settings.cpu_cores,
            memory_mb=settings.memory_mb,
            disk_size_gb=settings.disk_size_gb,
            disk_datastore_id=settings.disk_datastore_id,
            vm_id=settings.vm_id,
            description="Managed by Pulumi; Docker host for Portainer",
            tags=settings.tags,
            on_boot=True,
            started=True,
            pool_id=settings.pool_id,
            opts=child_opts,
        )

        host = host_from_cidr(settings.ip_address)
        connection = ConnectionArgs(
            host=host,
            port=22,
            user=settings.ssh_username,
            private_key=ssh_key.private_key_openssh,
        )
        vm_lifecycle = pulumi.Output.all(
            vm.vm_id,
            vm.mac_addresses,
            ssh_key.private_key_openssh,
        ).apply(json.dumps)
        fullchain_pem = pulumi.Output.all(certificate_pem, issuer_pem).apply(
            lambda parts: f"{parts[0].rstrip()}\n{parts[1].lstrip()}"
        )
        compose_yaml = _render_compose(settings.version, settings.public_port)
        auth_payload = pulumi.Output.all(admin_password.result).apply(
            lambda vals: json.dumps(
                asdict(
                    _PortainerAuthPayload(
                        Username=settings.admin_username,
                        Password=vals[0],
                    )
                )
            )
        )

        # --- provisioning chain (children of the VM) ---
        wait = self._command(
            name,
            rn,
            "wait-cloud-init",
            connection,
            create="cloud-init status --wait",
            triggers=[vm_lifecycle],
            parent=vm,
        )

        cert, key, compose = (
            self._command(
                name,
                rn,
                label,
                connection,
                create=_write_remote_file(path),
                stdin=content,
                triggers=[vm_lifecycle, content],
                depends_on=[wait],
                parent=vm,
            )
            for label, path, content in [
                ("write-cert", "/opt/portainer/certs/portainer.crt", fullchain_pem),
                ("write-key", "/opt/portainer/certs/portainer.key", private_key_pem),
                ("write-compose", "/opt/portainer/compose.yaml", compose_yaml),
            ]
        )

        deploy = self._command(
            name,
            rn,
            "deploy",
            connection,
            create=_DEPLOY_COMMAND,
            triggers=[
                vm_lifecycle,
                fullchain_pem,
                private_key_pem,
                compose_yaml,
                auth_payload,
            ],
            depends_on=[cert, key, compose],
            parent=vm,
        )

        self._command(
            name,
            rn,
            "init-admin",
            connection,
            create=_INIT_ADMIN_COMMAND,
            stdin=auth_payload,
            triggers=[
                vm_lifecycle,
                fullchain_pem,
                private_key_pem,
                compose_yaml,
                auth_payload,
            ],
            depends_on=[deploy],
            parent=vm,
        )

        self.admin_username = pulumi.Output.from_input(settings.admin_username)
        self.admin_password = pulumi.Output.secret(admin_password.result)
        self.ssh_private_key = pulumi.Output.secret(ssh_key.private_key_openssh)
        self.url = pulumi.Output.from_input(
            f"https://{settings.fqdn}:{settings.public_port}"
        )
        self.vm_id = vm.vm_id
        self.register_outputs(
            {
                "admin_username": self.admin_username,
                "admin_password": self.admin_password,
                "ssh_private_key": self.ssh_private_key,
                "url": self.url,
                "vm_id": self.vm_id,
            }
        )

    @staticmethod
    def _command(
        name: str,
        rn: str,
        label: str,
        connection: ConnectionArgs,
        *,
        create: pulumi.Input[str],
        triggers: list[pulumi.Input[str]],
        parent: pulumi.Resource,
        stdin: pulumi.Input[str] | None = None,
        depends_on: list[pulumi.Resource] | None = None,
    ) -> Command:
        return Command(
            f"{name}-{rn}-{label}",
            connection=connection,
            create=create,
            update=create,
            stdin=stdin,
            triggers=triggers,
            opts=pulumi.ResourceOptions(
                parent=parent,
                depends_on=depends_on or [],
            ),
        )
