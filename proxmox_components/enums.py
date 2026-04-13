"""Shared enumerations for Proxmox homelab components."""

from enum import StrEnum


class Datastore(StrEnum):
    """Default Proxmox storage identifiers."""

    LOCAL = "local"
    LOCAL_LVM = "local-lvm"
