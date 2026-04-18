"""Proxmox user and role component."""

from __future__ import annotations

from dataclasses import dataclass

import pulumi
import pulumi_random as random
from pulumi_proxmoxve._inputs import UserLegacyAclArgs
from pulumi_proxmoxve.role_legacy import RoleLegacy
from pulumi_proxmoxve.user_legacy import UserLegacy

from .base import ComponentBase


@dataclass(frozen=True)
class UserConfig:
    """Single Proxmox user definition."""

    username: str
    role_id: str
    pam_enabled: bool


OPERATIONS_ROLE_ID = "Operations"
OPERATIONS_PRIVILEGES = [
    "Datastore.Allocate",
    "Datastore.AllocateSpace",
    "Datastore.AllocateTemplate",
    "Datastore.Audit",
    "Group.Allocate",
    "Mapping.Audit",
    "Mapping.Use",
    "Pool.Allocate",
    "Pool.Audit",
    "Realm.AllocateUser",
    "SDN.Allocate",
    "SDN.Audit",
    "SDN.Use",
    "Sys.Audit",
    "Sys.Console",
    "Sys.Modify",
    "Sys.Syslog",
    "User.Modify",
    "VM.Allocate",
    "VM.Audit",
    "VM.Backup",
    "VM.Clone",
    "VM.Config.CDROM",
    "VM.Config.CPU",
    "VM.Config.Cloudinit",
    "VM.Config.Disk",
    "VM.Config.HWType",
    "VM.Config.Memory",
    "VM.Config.Network",
    "VM.Config.Options",
    "VM.Console",
    "VM.Migrate",
    "VM.PowerMgmt",
    "VM.Snapshot",
    "VM.Snapshot.Rollback",
]


class ProxmoxUsers(ComponentBase):
    """Manage Proxmox roles and users."""

    def __init__(
        self,
        name: str,
        users: list[UserConfig],
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        """Create the shared role and the requested users."""
        super().__init__(name, opts=opts)

        RoleLegacy(
            f"{name}-operations-role",
            role_id=OPERATIONS_ROLE_ID,
            privileges=OPERATIONS_PRIVILEGES,
            opts=pulumi.ResourceOptions(parent=self),
        )

        generated_passwords: dict[str, pulumi.Output[str]] = {}
        for user in users:
            password = random.RandomPassword(
                f"{name}-{user.username}-password",
                length=20,
                special=True,
                min_lower=1,
                min_numeric=1,
                min_special=1,
                min_upper=1,
                override_special="!#$%?-_",
                opts=pulumi.ResourceOptions(parent=self),
            )
            UserLegacy(
                f"{name}-{user.username}",
                comment=f"Managed by Pulumi; Proxmox user {user.username}",
                user_id=f"{user.username}@pam"
                if user.pam_enabled
                else f"{user.username}@pve",
                groups=[],
                password=password.result,
                acls=[
                    UserLegacyAclArgs(
                        path="/",
                        propagate=True,
                        role_id=user.role_id,
                    ),
                ],
                opts=pulumi.ResourceOptions(parent=self),
            )
            generated_passwords[user.username] = pulumi.Output.secret(password.result)

        self.generated_passwords = generated_passwords
        self.register_outputs({"generated_passwords": self.generated_passwords})
